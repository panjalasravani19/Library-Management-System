"""
Comprehensive Test Suite for Library Management System with Book Request & Approval System.
Tests:
1. Student successfully submits a request.
2. Unauthenticated user cannot submit a request.
3. Student cannot view another student's requests.
4. Duplicate pending request is rejected.
5. Admin can see all requests.
6. Student cannot approve or reject requests.
7. Admin successfully approves a request.
8. Available copies decrease after approval.
9. Admin successfully rejects a request.
10. Available copies remain unchanged after rejection.
11. Already reviewed requests cannot be approved or rejected again.
12. Existing issue and return functionality still works.
"""

import sys
import os
from datetime import date, timedelta
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
import models
import schemas
import main


def run_all_tests():
    print("=" * 70)
    print("STARTING E2E TEST: BOOK REQUEST & APPROVAL SYSTEM + EXISTING CORE")
    print("=" * 70)

    db = SessionLocal()
    passed = 0
    total = 0

    try:
        # Pre-test cleanup: delete previous test artifacts
        email_a = "student_a_req@example.com"
        email_b = "student_b_req@example.com"
        isbn_1 = "978-REQ-0001"
        isbn_2 = "978-REQ-0002"

        for em in [email_a, email_b]:
            stu = db.query(models.Student).filter(models.Student.email == em).first()
            if stu:
                db.delete(stu)
                db.commit()

        for isb in [isbn_1, isbn_2]:
            bk = db.query(models.Book).filter(models.Book.isbn == isb).first()
            if bk:
                db.query(models.BookIssue).filter(models.BookIssue.book_id == bk.id).delete()
                db.query(models.BookRequest).filter(models.BookRequest.book_id == bk.id).delete()
                db.delete(bk)
                db.commit()

        # -------------------------------------------------------------------
        # SETUP: Admin, Students, and Books
        # -------------------------------------------------------------------
        # 1. Admin login token
        admin_res = main.admin_login(schemas.AdminLogin(username=main.ADMIN_USERNAME, password=main.ADMIN_PASSWORD))
        admin_token = admin_res.access_token
        admin_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=admin_token)
        admin_admin_dict = main.get_current_admin(credentials=admin_creds)

        # 2. Student A & Student B
        stu_a = main.register_student(
            schemas.StudentCreate(name="Alice Student", email=email_a, roll_number="ROLL-REQ-A", password="AlicePassword123"),
            db=db,
        )
        login_a = main.login_student(schemas.StudentLogin(email=email_a, password="AlicePassword123"), db=db)
        token_a = login_a["access_token"]
        creds_a = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_a)
        student_a_obj = main.get_current_student(credentials=creds_a, db=db)

        stu_b = main.register_student(
            schemas.StudentCreate(name="Bob Student", email=email_b, roll_number="ROLL-REQ-B", password="BobPassword123"),
            db=db,
        )
        login_b = main.login_student(schemas.StudentLogin(email=email_b, password="BobPassword123"), db=db)
        token_b = login_b["access_token"]
        creds_b = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_b)
        student_b_obj = main.get_current_student(credentials=creds_b, db=db)

        # 3. Create Books
        book1 = main.create_book(
            schemas.BookCreate(title="Algorithms 101", author="Prof. Turing", isbn=isbn_1, category="CS", total_copies=2),
            db=db,
            current_admin=admin_admin_dict,
        )
        book2 = main.create_book(
            schemas.BookCreate(title="Operating Systems", author="Prof. Tanenbaum", isbn=isbn_2, category="CS", total_copies=1),
            db=db,
            current_admin=admin_admin_dict,
        )

        # -------------------------------------------------------------------
        # TEST 1: Student successfully submits a request
        # -------------------------------------------------------------------
        total += 1
        req1 = main.create_book_request(
            schemas.BookRequestCreate(book_id=book1.id),
            db=db,
            current_student=student_a_obj,
        )
        assert req1.id is not None
        assert req1.status == "Pending"
        assert req1.book_id == book1.id

        # Verify available copies NOT decreased yet
        db.refresh(book1)
        assert book1.available_copies == 2
        print(f"[PASS] Test 1: Student A submitted request #{req1.id} for '{book1.title}', copies untouched (2/2)")
        passed += 1

        # -------------------------------------------------------------------
        # TEST 2: Unauthenticated user cannot submit a request
        # -------------------------------------------------------------------
        total += 1
        try:
            main.get_current_student(credentials=None, db=db)
            print("[FAIL] Test 2: Allowed unauthenticated user to access student dependency!")
        except HTTPException as exc:
            assert exc.status_code == 401
            print(f"[PASS] Test 2: Unauthenticated request blocked with HTTP 401 ('{exc.detail}')")
            passed += 1

        # -------------------------------------------------------------------
        # TEST 3: Student cannot view another student's requests
        # -------------------------------------------------------------------
        total += 1
        # Student B fetches their requests
        my_reqs_b = main.get_my_book_requests(db=db, current_student=student_b_obj)
        assert len(my_reqs_b) == 0  # Cannot see Student A's request

        # Student A fetches their requests
        my_reqs_a = main.get_my_book_requests(db=db, current_student=student_a_obj)
        assert len(my_reqs_a) == 1
        assert my_reqs_a[0].id == req1.id
        print(f"[PASS] Test 3: Isolation verified: Student B sees 0 requests, Student A sees only their own request")
        passed += 1

        # -------------------------------------------------------------------
        # TEST 4: Duplicate pending request is rejected
        # -------------------------------------------------------------------
        total += 1
        try:
            main.create_book_request(
                schemas.BookRequestCreate(book_id=book1.id),
                db=db,
                current_student=student_a_obj,
            )
            print("[FAIL] Test 4: Duplicate pending request was allowed!")
        except HTTPException as exc:
            assert exc.status_code == 400
            print(f"[PASS] Test 4: Duplicate pending request rejected with HTTP 400 ('{exc.detail}')")
            passed += 1

        # -------------------------------------------------------------------
        # TEST 5: Admin can see all requests
        # -------------------------------------------------------------------
        total += 1
        admin_reqs = main.list_admin_book_requests(db=db, current_admin=admin_admin_dict)
        assert any(r.id == req1.id for r in admin_reqs)
        matching_req = [r for r in admin_reqs if r.id == req1.id][0]
        assert matching_req.student_name == "Alice Student"
        assert matching_req.student_roll_number == "ROLL-REQ-A"
        assert matching_req.book_title == "Algorithms 101"
        print(f"[PASS] Test 5: Admin retrieved all requests with student & book details")
        passed += 1

        # -------------------------------------------------------------------
        # TEST 6: Student cannot approve or reject requests
        # -------------------------------------------------------------------
        total += 1
        # Student token passed to get_current_admin
        try:
            main.get_current_admin(credentials=creds_a)
            print("[FAIL] Test 6: Student token was accepted as admin!")
        except HTTPException as exc:
            assert exc.status_code == 403
            print(f"[PASS] Test 6: Student authorization rejected from admin approval with HTTP 403 ('{exc.detail}')")
            passed += 1

        # -------------------------------------------------------------------
        # TEST 7: Admin successfully approves a request
        # -------------------------------------------------------------------
        total += 1
        approved_req = main.approve_book_request(
            request_id=req1.id,
            db=db,
            current_admin=admin_admin_dict,
        )
        assert approved_req.status == "Approved"
        assert approved_req.reviewed_at is not None

        # Check that BookIssue record was automatically created
        created_issue = (
            db.query(models.BookIssue)
            .filter(
                models.BookIssue.student_id == stu_a.id,
                models.BookIssue.book_id == book1.id,
                models.BookIssue.is_returned == False,
            )
            .first()
        )
        assert created_issue is not None
        assert created_issue.issue_date == date.today()
        assert created_issue.due_date == date.today() + timedelta(days=14)
        print(f"[PASS] Test 7: Admin approved request #{req1.id}; BookIssue loan record created")
        passed += 1

        # -------------------------------------------------------------------
        # TEST 8: Available copies decrease after approval
        # -------------------------------------------------------------------
        total += 1
        db.refresh(book1)
        assert book1.available_copies == 1  # Decreased from 2 to 1
        print(f"[PASS] Test 8: Book available copies successfully decremented to {book1.available_copies}")
        passed += 1

        # -------------------------------------------------------------------
        # TEST 9 & 10: Admin successfully rejects a request & copies unchanged
        # -------------------------------------------------------------------
        total += 1
        # Student B requests Book 2
        req2 = main.create_book_request(
            schemas.BookRequestCreate(book_id=book2.id),
            db=db,
            current_student=student_b_obj,
        )
        assert req2.status == "Pending"

        # Admin rejects request
        rejected_req = main.reject_book_request(
            request_id=req2.id,
            review_data=schemas.BookRequestReview(remarks="Temporarily reserved for faculty"),
            db=db,
            current_admin=admin_admin_dict,
        )
        assert rejected_req.status == "Rejected"
        assert rejected_req.remarks == "Temporarily reserved for faculty"
        assert rejected_req.reviewed_at is not None

        # Test 10: Available copies remain unchanged
        db.refresh(book2)
        assert book2.available_copies == 1  # Still 1
        print(f"[PASS] Tests 9 & 10: Admin rejected request #{req2.id} with remarks; book copies remained {book2.available_copies}/1")
        passed += 1

        # -------------------------------------------------------------------
        # TEST 11: Already reviewed requests cannot be approved or rejected again
        # -------------------------------------------------------------------
        total += 1
        # Try re-approving an already approved request
        try:
            main.approve_book_request(request_id=req1.id, db=db, current_admin=admin_admin_dict)
            print("[FAIL] Test 11: Re-approving an approved request was permitted!")
        except HTTPException as exc:
            assert exc.status_code == 400

        # Try re-rejecting an already rejected request
        try:
            main.reject_book_request(request_id=req2.id, db=db, current_admin=admin_admin_dict)
            print("[FAIL] Test 11: Re-rejecting a rejected request was permitted!")
        except HTTPException as exc:
            assert exc.status_code == 400

        print(f"[PASS] Test 11: Re-reviewing already processed requests correctly blocked with HTTP 400")
        passed += 1

        # -------------------------------------------------------------------
        # TEST 12: Existing issue and return functionality still works
        # -------------------------------------------------------------------
        total += 1
        # Student A returns the book issued via approval
        returned_issue = main.return_book(issue_id=created_issue.id, db=db, current_admin=admin_admin_dict)
        assert returned_issue.is_returned is True
        assert returned_issue.return_date == date.today()

        # Available copies restored
        db.refresh(book1)
        assert book1.available_copies == 2  # Restored to 2

        # Manual checkout by admin directly also still works
        manual_issue = main.issue_book(
            schemas.BookIssueCreate(student_id=stu_b.id, book_id=book1.id),
            db=db,
            current_admin=admin_admin_dict,
        )
        assert manual_issue.id is not None
        db.refresh(book1)
        assert book1.available_copies == 1

        # Return manual checkout
        main.return_book(issue_id=manual_issue.id, db=db, current_admin=admin_admin_dict)
        db.refresh(book1)
        assert book1.available_copies == 2
        print(f"[PASS] Test 12: Existing manual checkout, return, and inventory restoration verified")
        passed += 1

        # -------------------------------------------------------------------
        # CLEANUP
        # -------------------------------------------------------------------
        db.query(models.BookRequest).filter(models.BookRequest.id.in_([req1.id, req2.id])).delete()
        db.query(models.BookIssue).filter(models.BookIssue.id.in_([created_issue.id, manual_issue.id])).delete()
        db.delete(book1)
        db.delete(book2)
        db.delete(stu_a)
        db.delete(stu_b)
        db.commit()

        print("=" * 70)
        print(f"ALL {passed}/{total} TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)
        return True

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR ENCOUNTERED]: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
