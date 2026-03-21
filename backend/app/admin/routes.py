"""Admin routes for company approval workflow."""

from flask import Blueprint, jsonify

from app.auth.utils import role_required
from app.models import Company, db

admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.get("/companies/pending")
@role_required("admin")
def list_pending_companies():
    """List all companies waiting for admin approval."""
    companies = (
        Company.query
        .filter_by(approval_status="pending")
        .order_by(Company.company_id.desc())
        .all()
    )

    return jsonify([
        {
            "company_id": c.company_id,
            "company_name": c.company_name,
            "website": c.website,
            "approval_status": c.approval_status,
        }
        for c in companies
    ]), 200


@admin_bp.put("/company/<int:company_id>/approve")
@role_required("admin")
def approve_company(company_id):
    """Approve a company registration request."""
    company = db.session.get(Company, company_id)

    if not company:
        return jsonify({"error": "Company not found"}), 404

    if company.approval_status != "pending":
        return jsonify({"error": "Company already processed"}), 400

    company.approval_status = "approved"
    db.session.commit()

    return jsonify({"message": "Company approved successfully"}), 200


@admin_bp.put("/company/<int:company_id>/reject")
@role_required("admin")
def reject_company(company_id):
    """Reject a company registration request."""
    company = db.session.get(Company, company_id)

    if not company:
        return jsonify({"error": "Company not found"}), 404

    if company.approval_status != "pending":
        return jsonify({"error": "Company already processed"}), 400

    company.approval_status = "rejected"
    db.session.commit()

    return jsonify({"message": "Company rejected successfully"}), 200


__all__ = ["admin_bp"]