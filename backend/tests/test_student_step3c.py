from datetime import date, datetime, timedelta, timezone

from flask_jwt_extended import create_access_token

from app.models import (
    Application,
    Company,
    Placement,
    PlacementDrive,
    PlacementOffer,
    Student,
    User,
    db,
)


def _make_user(username, email, role):
    user = User(username=username, email=email, role=role, is_active=True)
    user.set_password('Password@123')
    db.session.add(user)
    db.session.flush()
    return user


def _make_company_profile(user_id, name, hr_email):
    company = Company(
        user_id=user_id,
        company_name=name,
        industry='Software',
        hr_contact_name='Hiring Lead',
        hr_contact_email=hr_email,
        hr_contact_phone='9999999999',
        approval_status='approved',
    )
    db.session.add(company)
    db.session.flush()
    return company


def _make_student_profile(user_id, roll_number, branch='CSE', year=4, cgpa=8.2):
    student = Student(
        user_id=user_id,
        roll_number=roll_number,
        branch=branch,
        year=year,
        cgpa=cgpa,
        profile_completed=True,
    )
    db.session.add(student)
    db.session.flush()
    return student


def _make_drive(
    company_id,
    title='Backend Engineer',
    status='approved',
    min_cgpa=6.0,
    eligible_branches=None,
    eligible_years=None,
):
    drive = PlacementDrive(
        company_id=company_id,
        job_title=title,
        job_description='Core job responsibilities',
        required_skills='Python,SQL,APIs',
        experience_required='0-2 years',
        benefits='Health insurance and flexible hours',
        min_cgpa=min_cgpa,
        eligible_branches=eligible_branches or ['CSE', 'ECE'],
        eligible_years=eligible_years or [3, 4],
        salary_lpa=14.0,
        job_location='Remote',
        application_deadline=datetime.now(timezone.utc) + timedelta(days=10),
        interview_mode='online',
        status=status,
    )
    db.session.add(drive)
    db.session.flush()
    return drive


def _auth_headers(user_id, role):
    token = create_access_token(identity=str(user_id), additional_claims={'role': role})
    return {'Authorization': f'Bearer {token}'}


def test_student_can_list_drives_and_apply_once(app, client):
    with app.app_context():
        company_user = _make_user('company.step3c.a', 'company.step3c.a@example.com', 'company')
        company = _make_company_profile(
            company_user.user_id,
            'Step3C Drives Inc',
            'hr.step3c.a@example.com',
        )

        eligible_drive = _make_drive(
            company.company_id,
            title='Platform Engineer',
            min_cgpa=7.5,
            eligible_branches=['CSE', 'ECE'],
            eligible_years=[4],
        )
        _make_drive(
            company.company_id,
            title='Analytics Specialist',
            min_cgpa=9.0,
            eligible_branches=['ECE'],
            eligible_years=[4],
        )

        student_user = _make_user('student.step3c.a', 'student.step3c.a@example.com', 'student')
        student = _make_student_profile(
            student_user.user_id,
            'CS21B9302',
            branch='CSE',
            year=4,
            cgpa=8.1,
        )

        db.session.commit()
        headers = _auth_headers(student_user.user_id, 'student')

        student_id = student.student_id
        eligible_drive_id = eligible_drive.drive_id

    list_response = client.get('/student/drives', headers=headers)
    assert list_response.status_code == 200

    payload = list_response.get_json()['data']
    assert payload['total'] == 2

    listed = {item['drive_id']: item for item in payload['items']}
    assert listed[eligible_drive_id]['is_eligible'] is True
    assert listed[eligible_drive_id]['already_applied'] is False

    apply_response = client.post(f'/student/drives/{eligible_drive_id}/apply', headers=headers)
    assert apply_response.status_code == 201

    apply_payload = apply_response.get_json()['data']
    assert apply_payload['already_applied'] is False
    assert apply_payload['application']['status'] == 'applied'

    second_apply = client.post(f'/student/drives/{eligible_drive_id}/apply', headers=headers)
    assert second_apply.status_code == 200
    assert second_apply.get_json()['data']['already_applied'] is True

    with app.app_context():
        app_count = Application.query.filter_by(
            student_id=student_id,
            drive_id=eligible_drive_id,
        ).count()
        assert app_count == 1


def test_student_apply_rejected_when_not_eligible(app, client):
    with app.app_context():
        company_user = _make_user('company.step3c.b', 'company.step3c.b@example.com', 'company')
        company = _make_company_profile(
            company_user.user_id,
            'Step3C Eligibility Inc',
            'hr.step3c.b@example.com',
        )
        ineligible_drive = _make_drive(
            company.company_id,
            title='ML Engineer',
            min_cgpa=9.3,
            eligible_branches=['CSE'],
            eligible_years=[4],
        )

        student_user = _make_user('student.step3c.b', 'student.step3c.b@example.com', 'student')
        _make_student_profile(
            student_user.user_id,
            'CS21B9303',
            branch='CSE',
            year=4,
            cgpa=8.0,
        )

        db.session.commit()
        headers = _auth_headers(student_user.user_id, 'student')
        drive_id = ineligible_drive.drive_id

    response = client.post(f'/student/drives/{drive_id}/apply', headers=headers)
    assert response.status_code == 400
    assert 'Minimum CGPA is' in response.get_json()['error']


def test_student_history_and_documents_are_available(app, client):
    with app.app_context():
        company_user = _make_user('company.step3c.c', 'company.step3c.c@example.com', 'company')
        company = _make_company_profile(
            company_user.user_id,
            'Step3C History Inc',
            'hr.step3c.c@example.com',
        )
        drive = _make_drive(company.company_id, title='SRE Engineer')
        alternate_drive = _make_drive(company.company_id, title='Data Engineer')

        student_user = _make_user('student.step3c.c', 'student.step3c.c@example.com', 'student')
        student = _make_student_profile(student_user.user_id, 'CS21B9304')

        selected_app = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status='selected',
        )
        rejected_app = Application(
            student_id=student.student_id,
            drive_id=alternate_drive.drive_id,
            status='rejected',
            rejection_reason='Position filled',
        )
        db.session.add_all([selected_app, rejected_app])
        db.session.flush()

        offer = PlacementOffer(
            application_id=selected_app.application_id,
            student_id=student.student_id,
            company_id=company.company_id,
            drive_id=drive.drive_id,
            salary=2000000,
            position='Site Reliability Engineer',
            joining_date=date.today() + timedelta(days=40),
            status='offered',
        )
        db.session.add(offer)
        db.session.flush()

        placement = Placement(
            student_id=student.student_id,
            company_id=company.company_id,
            drive_id=drive.drive_id,
            position='Site Reliability Engineer',
            salary=2100000,
            joining_date=date.today() + timedelta(days=60),
        )
        db.session.add(placement)
        db.session.commit()

        headers = _auth_headers(student_user.user_id, 'student')
        offer_id = offer.offer_id
        placement_id = placement.placement_id

    history_response = client.get('/student/history', headers=headers)
    assert history_response.status_code == 200

    history_payload = history_response.get_json()['data']
    assert history_payload['summary']['total_applied'] == 2
    assert history_payload['summary']['offers_received'] == 1
    assert history_payload['summary']['placements_count'] == 1
    assert history_payload['summary']['highest_package'] == 2100000.0

    offer_document = client.get(f'/student/offers/{offer_id}/document', headers=headers)
    assert offer_document.status_code == 200
    assert 'offer-letter-' in offer_document.headers.get('Content-Disposition', '')
    assert b'Recruitify Offer Letter' in offer_document.data

    placement_document = client.get(
        f'/student/placements/{placement_id}/document',
        headers=headers,
    )
    assert placement_document.status_code == 200
    assert 'placement-confirmation-' in placement_document.headers.get('Content-Disposition', '')
    assert b'Recruitify Placement Confirmation' in placement_document.data
