"""Admin routes for dashboard and management module."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.auth.utils import role_required

from . import services

admin_bp = Blueprint("admin_bp", __name__)
MAX_LIMIT = 100


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


def _json_result(service_result):
    payload, status_code = service_result
    return jsonify(payload), status_code


@admin_bp.get("/dashboard")
@jwt_required()
@role_required("admin")
def dashboard():
    return _json_result(services.get_dashboard_stats())


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
    return _json_result(services.approve_company(company_id))


@admin_bp.put("/company/<int:company_id>/reject")
@jwt_required()
@role_required("admin")
def reject_company(company_id):
    return _json_result(services.reject_company(company_id))


@admin_bp.delete("/company/<int:company_id>")
@jwt_required()
@role_required("admin")
def delete_company(company_id):
    return _json_result(services.soft_delete_company(company_id))


@admin_bp.put("/company/<int:company_id>/deactivate")
@jwt_required()
@role_required("admin")
def deactivate_company(company_id):
    return _json_result(services.deactivate_company(company_id))


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
    return _json_result(services.deactivate_student(student_id))


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

    return _json_result(services.list_jobs(page, limit, sort_by, order, company_id))


@admin_bp.put("/job/<int:job_id>/approve")
@jwt_required()
@role_required("admin")
def approve_job(job_id):
    return _json_result(services.approve_job(job_id))


@admin_bp.put("/job/<int:job_id>/reject")
@jwt_required()
@role_required("admin")
def reject_job(job_id):
    return _json_result(services.reject_job(job_id))


@admin_bp.delete("/job/<int:job_id>")
@jwt_required()
@role_required("admin")
def delete_job(job_id):
    return _json_result(services.soft_delete_job(job_id))


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

    return _json_result(
        services.search_companies(query_text, page, limit, sort_by, order)
    )


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

    return _json_result(
        services.search_students(query_text, page, limit, sort_by, order)
    )


@admin_bp.get("/applications")
@jwt_required()
@role_required("admin")
def list_applications():
    page, limit, sort_by, order, error = _parse_pagination_and_sort()
    if error:
        message, status_code = error
        return jsonify({"success": False, "error": message}), status_code

    return _json_result(services.list_applications(page, limit, sort_by, order))


__all__ = ["admin_bp"]