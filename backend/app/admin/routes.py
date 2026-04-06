"""Admin routes for dashboard and management module."""

from urllib.parse import urlencode

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.cache import (
    CACHE_NAMESPACE_ADMIN_COMPANY_SEARCH,
    CACHE_NAMESPACE_ADMIN_JOBS,
    CACHE_NAMESPACE_ADMIN_STUDENT_SEARCH,
    invalidate_api_cache_namespaces,
)
from app.auth.utils import role_required

from . import services

admin_bp = Blueprint("admin_bp", __name__)
MAX_LIMIT = 100
MAX_ANALYTICS_MONTHS = 24

CACHE_NAMESPACE_JOBS = CACHE_NAMESPACE_ADMIN_JOBS
CACHE_NAMESPACE_COMPANY_SEARCH = CACHE_NAMESPACE_ADMIN_COMPANY_SEARCH
CACHE_NAMESPACE_STUDENT_SEARCH = CACHE_NAMESPACE_ADMIN_STUDENT_SEARCH


def _parse_pagination_and_sort():
    page_raw = request.args.get("page", "1")
    limit_raw = request.args.get("limit", "10")
    sort_by = request.args.get("sort_by", "created_at").strip()
    order = request.args.get("order", "desc").strip().lower()

    try:
        page = int(page_raw)
        limit = int(limit_raw)
    except (TypeError, ValueError):
        return None, None, None, None, ("page and limit must be integers", 400)

    if page < 1:
        return None, None, None, None, ("page must be greater than 0", 400)
    if limit < 1:
        return None, None, None, None, ("limit must be greater than 0", 400)
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT

    return page, limit, sort_by, order, None


def _parse_pagination():
    page_raw = request.args.get("page", "1")
    limit_raw = request.args.get("limit", "10")

    try:
        page = int(page_raw)
        limit = int(limit_raw)
    except (TypeError, ValueError):
        return None, None, ("page and limit must be integers", 400)

    if page < 1:
        return None, None, ("page must be greater than 0", 400)
    if limit < 1:
        return None, None, ("limit must be greater than 0", 400)

    return page, min(limit, MAX_LIMIT), None


def _parse_months_query(default_value=6):
    raw_value = request.args.get("months")
    if raw_value is None or str(raw_value).strip() == "":
        return default_value, None

    try:
        months = int(raw_value)
    except (TypeError, ValueError):
        return None, ("months must be an integer", 400)

    if months < 1 or months > MAX_ANALYTICS_MONTHS:
        return None, (
            f"months must be between 1 and {MAX_ANALYTICS_MONTHS}",
            400,
        )

    return months, None


def _json_result(service_result):
    payload, status_code = service_result
    return jsonify(payload), status_code


def _current_user_id():
    identity = get_jwt_identity()
    try:
        return int(identity)
    except (TypeError, ValueError):
        return None


def _cache_extension():
    return current_app.extensions.get("redis_cache")


def _cache_suffix_for_request():
    sorted_pairs = []
    for key in sorted(request.args.keys()):
        values = sorted(request.args.getlist(key))
        for value in values:
            sorted_pairs.append((key, value))

    query_string = urlencode(sorted_pairs, doseq=True)
    user_id = _current_user_id()
    return f"admin={user_id}|{query_string}"


def _cache_lookup(namespace):
    cache = _cache_extension()
    if not cache or not getattr(cache, "is_available", False):
        return None, None

    cache_key = cache.make_key(namespace, _cache_suffix_for_request())
    cached_value = cache.get_json(cache_key)
    if not isinstance(cached_value, dict):
        return cache_key, None

    payload = cached_value.get("payload")
    status_code = cached_value.get("status_code", 200)
    if not isinstance(payload, dict):
        return cache_key, None

    try:
        status_code = int(status_code)
    except (TypeError, ValueError):
        status_code = 200

    return cache_key, (payload, status_code)


def _cache_store(cache_key, service_result, ttl_config_key):
    if not cache_key:
        return

    cache = _cache_extension()
    if not cache or not getattr(cache, "is_available", False):
        return

    payload, status_code = service_result
    if status_code != 200 or not isinstance(payload, dict) or not payload.get("success"):
        return

    ttl_seconds = current_app.config.get(
        ttl_config_key,
        current_app.config.get("CACHE_DEFAULT_TTL_SECONDS", 120),
    )
    cache.set_json(
        cache_key,
        {"payload": payload, "status_code": status_code},
        ttl_seconds,
    )


def _service_result_success(service_result):
    payload, status_code = service_result
    if status_code < 200 or status_code >= 300:
        return False
    if isinstance(payload, dict):
        return bool(payload.get("success", True))
    return True


def _invalidate_cache_namespaces(*namespaces):
    invalidate_api_cache_namespaces(_cache_extension(), *namespaces)


@admin_bp.get("/dashboard")
@jwt_required()
@role_required("admin")
def dashboard():
    return _json_result(services.get_dashboard_stats())


@admin_bp.get("/analytics/overview")
@jwt_required()
@role_required("admin")
def analytics_overview():
    months, error = _parse_months_query()
    if error:
        message, status_code = error
        return jsonify({"success": False, "error": message}), status_code

    return _json_result(services.get_analytics_overview(months=months))


@admin_bp.get("/public/landing-dashboard")
def public_landing_dashboard():
    months, error = _parse_months_query()
    if error:
        message, status_code = error
        return jsonify({"success": False, "error": message}), status_code

    return _json_result(services.get_public_landing_dashboard(months=months))


@admin_bp.get("/activity-logs")
@jwt_required()
@role_required("admin")
def list_activity_logs():
    limit_raw = request.args.get("limit", "20")
    try:
        limit = int(limit_raw)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "limit must be an integer"}), 400

    if limit < 1:
        return jsonify({"success": False, "error": "limit must be greater than 0"}), 400

    return _json_result(services.list_activity_logs(limit))


@admin_bp.get("/notifications")
@jwt_required()
@role_required("admin")
def list_notifications():
    admin_user_id = _current_user_id()
    if admin_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401

    page, limit, error = _parse_pagination()
    if error:
        message, status_code = error
        return jsonify({"success": False, "error": message}), status_code

    read_filter = (request.args.get("is_read") or "all").strip().lower()
    return _json_result(
        services.list_notifications(admin_user_id, page, limit, read_filter)
    )


@admin_bp.put("/notifications/<int:notification_id>/read")
@jwt_required()
@role_required("admin")
def mark_notification_read(notification_id):
    admin_user_id = _current_user_id()
    if admin_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401

    return _json_result(
        services.mark_notification_read(admin_user_id, notification_id)
    )


@admin_bp.put("/notifications/read-all")
@jwt_required()
@role_required("admin")
def mark_all_notifications_read():
    admin_user_id = _current_user_id()
    if admin_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401

    return _json_result(services.mark_all_notifications_read(admin_user_id))


@admin_bp.get("/companies")
@jwt_required()
@role_required("admin")
def list_companies():
    page, limit, sort_by, order, error = _parse_pagination_and_sort()
    if error:
        message, status_code = error
        return jsonify({"success": False, "error": message}), status_code

    return _json_result(services.list_companies(page, limit, sort_by, order))


@admin_bp.put("/company/<int:company_id>/approve")
@jwt_required()
@role_required("admin")
def approve_company(company_id):
    actor_user_id = _current_user_id()
    if actor_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401
    service_result = services.approve_company(company_id, actor_user_id)
    if _service_result_success(service_result):
        _invalidate_cache_namespaces(CACHE_NAMESPACE_COMPANY_SEARCH)
    return _json_result(service_result)


@admin_bp.put("/company/<int:company_id>/reject")
@jwt_required()
@role_required("admin")
def reject_company(company_id):
    actor_user_id = _current_user_id()
    if actor_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401
    service_result = services.reject_company(company_id, actor_user_id)
    if _service_result_success(service_result):
        _invalidate_cache_namespaces(CACHE_NAMESPACE_COMPANY_SEARCH)
    return _json_result(service_result)


@admin_bp.delete("/company/<int:company_id>")
@jwt_required()
@role_required("admin")
def delete_company(company_id):
    actor_user_id = _current_user_id()
    if actor_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401
    service_result = services.soft_delete_company(company_id, actor_user_id)
    if _service_result_success(service_result):
        _invalidate_cache_namespaces(CACHE_NAMESPACE_COMPANY_SEARCH)
    return _json_result(service_result)


@admin_bp.put("/company/<int:company_id>/deactivate")
@jwt_required()
@role_required("admin")
def deactivate_company(company_id):
    actor_user_id = _current_user_id()
    if actor_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401
    service_result = services.deactivate_company(company_id, actor_user_id)
    if _service_result_success(service_result):
        _invalidate_cache_namespaces(CACHE_NAMESPACE_COMPANY_SEARCH)
    return _json_result(service_result)


@admin_bp.put("/company/<int:company_id>/activate")
@jwt_required()
@role_required("admin")
def activate_company(company_id):
    actor_user_id = _current_user_id()
    if actor_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401
    service_result = services.activate_company(company_id, actor_user_id)
    if _service_result_success(service_result):
        _invalidate_cache_namespaces(CACHE_NAMESPACE_COMPANY_SEARCH)
    return _json_result(service_result)


@admin_bp.get("/students")
@jwt_required()
@role_required("admin")
def list_students():
    page, limit, sort_by, order, error = _parse_pagination_and_sort()
    if error:
        message, status_code = error
        return jsonify({"success": False, "error": message}), status_code

    return _json_result(services.list_students(page, limit, sort_by, order))


@admin_bp.put("/student/<int:student_id>/deactivate")
@jwt_required()
@role_required("admin")
def deactivate_student(student_id):
    actor_user_id = _current_user_id()
    if actor_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401
    service_result = services.deactivate_student(student_id, actor_user_id)
    if _service_result_success(service_result):
        _invalidate_cache_namespaces(CACHE_NAMESPACE_STUDENT_SEARCH)
    return _json_result(service_result)


@admin_bp.put("/student/<int:student_id>/activate")
@jwt_required()
@role_required("admin")
def activate_student(student_id):
    actor_user_id = _current_user_id()
    if actor_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401
    service_result = services.activate_student(student_id, actor_user_id)
    if _service_result_success(service_result):
        _invalidate_cache_namespaces(CACHE_NAMESPACE_STUDENT_SEARCH)
    return _json_result(service_result)


@admin_bp.get("/jobs")
@jwt_required()
@role_required("admin")
def list_jobs():
    company_id_raw = request.args.get("company_id")
    company_id = None
    if company_id_raw is not None and company_id_raw != "":
        try:
            company_id = int(company_id_raw)
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "company_id must be an integer"}), 400
        if company_id < 1:
            return jsonify({"success": False, "error": "company_id must be greater than 0"}), 400

    page, limit, sort_by, order, error = _parse_pagination_and_sort()
    if error:
        message, status_code = error
        return jsonify({"success": False, "error": message}), status_code

    cache_key, cached_result = _cache_lookup(CACHE_NAMESPACE_JOBS)
    if cached_result:
        payload, status_code = cached_result
        return jsonify(payload), status_code

    service_result = services.list_jobs(page, limit, sort_by, order, company_id)
    _cache_store(cache_key, service_result, "CACHE_JOBS_LIST_TTL_SECONDS")
    return _json_result(service_result)


@admin_bp.put("/job/<int:job_id>/approve")
@jwt_required()
@role_required("admin")
def approve_job(job_id):
    actor_user_id = _current_user_id()
    if actor_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401
    service_result = services.approve_job(job_id, actor_user_id)
    if _service_result_success(service_result):
        _invalidate_cache_namespaces(CACHE_NAMESPACE_JOBS)
    return _json_result(service_result)


@admin_bp.put("/job/<int:job_id>/reject")
@jwt_required()
@role_required("admin")
def reject_job(job_id):
    actor_user_id = _current_user_id()
    if actor_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401
    service_result = services.reject_job(job_id, actor_user_id)
    if _service_result_success(service_result):
        _invalidate_cache_namespaces(CACHE_NAMESPACE_JOBS)
    return _json_result(service_result)


@admin_bp.delete("/job/<int:job_id>")
@jwt_required()
@role_required("admin")
def delete_job(job_id):
    actor_user_id = _current_user_id()
    if actor_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401
    service_result = services.soft_delete_job(job_id, actor_user_id)
    if _service_result_success(service_result):
        _invalidate_cache_namespaces(CACHE_NAMESPACE_JOBS)
    return _json_result(service_result)


@admin_bp.get("/search/companies")
@jwt_required()
@role_required("admin")
def search_companies():
    query_text = (request.args.get("q") or "").strip()
    if not query_text:
        return jsonify({"success": False, "error": "q is required"}), 400

    page, limit, sort_by, order, error = _parse_pagination_and_sort()
    if error:
        message, status_code = error
        return jsonify({"success": False, "error": message}), status_code

    cache_key, cached_result = _cache_lookup(CACHE_NAMESPACE_COMPANY_SEARCH)
    if cached_result:
        payload, status_code = cached_result
        return jsonify(payload), status_code

    service_result = services.search_companies(query_text, page, limit, sort_by, order)
    _cache_store(cache_key, service_result, "CACHE_COMPANY_SEARCH_TTL_SECONDS")
    return _json_result(service_result)


@admin_bp.get("/search/students")
@jwt_required()
@role_required("admin")
def search_students():
    query_text = (request.args.get("q") or "").strip()
    if not query_text:
        return jsonify({"success": False, "error": "q is required"}), 400

    page, limit, sort_by, order, error = _parse_pagination_and_sort()
    if error:
        message, status_code = error
        return jsonify({"success": False, "error": message}), status_code

    cache_key, cached_result = _cache_lookup(CACHE_NAMESPACE_STUDENT_SEARCH)
    if cached_result:
        payload, status_code = cached_result
        return jsonify(payload), status_code

    service_result = services.search_students(query_text, page, limit, sort_by, order)
    _cache_store(cache_key, service_result, "CACHE_STUDENT_SEARCH_TTL_SECONDS")
    return _json_result(service_result)


@admin_bp.get("/applications")
@jwt_required()
@role_required("admin")
def list_applications():
    page, limit, sort_by, order, error = _parse_pagination_and_sort()
    if error:
        message, status_code = error
        return jsonify({"success": False, "error": message}), status_code

    return _json_result(services.list_applications(page, limit, sort_by, order))


@admin_bp.put("/application/<int:application_id>/status")
@jwt_required()
@role_required("admin")
def update_application_status(application_id):
    actor_user_id = _current_user_id()
    if actor_user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401

    payload = request.get_json(silent=True) or {}
    status = (payload.get("status") or "").strip()
    if not status:
        return jsonify({"success": False, "error": "status is required"}), 400

    rejection_reason = payload.get("rejection_reason")
    notes = payload.get("notes")
    return _json_result(
        services.update_application_status(
            application_id,
            status,
            rejection_reason,
            notes,
            actor_user_id=actor_user_id,
        )
    )


__all__ = ["admin_bp"]