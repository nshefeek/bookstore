from uuid import UUID
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from bookstore.auth.models import User, UserRole
from bookstore.auth.dependencies import get_current_active_user, user_is_librarian_or_admin

from .dependencies import get_borrow_service
from .schemas import (
    BookRequestCreate,
    BookRequestResponse,
    BookRequestFilter,
    BorrowHistoryFilter,
    BorrowRecordCreate,
    BorrowRecordResponse,
    ReturnRequest,
    BorrowRecordDetail,
)
from .services import BorrowService


router = APIRouter()


@router.post(
    "/borrow",
    response_model=BorrowRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Borrow a book",
    tags=["borrowing"],
)
async def borrow(
    borrow_data: BorrowRecordCreate,
    user: User = Depends(get_current_active_user),
    service: BorrowService = Depends(get_borrow_service),
):  
    borrow_data.user_id = user.id
    record = await service.borrow_book(borrow_data)
    record_details = await service.get_borrow_details(record.id)
    return BorrowRecordResponse(**record_details)


@router.post(
    "/return",
    response_model=BorrowRecordDetail,
    status_code=status.HTTP_200_OK,
    summary="Return a book",
    tags=["borrowing"],
)
async def return_book(
    borrow_record: ReturnRequest,
    user: User = Depends(get_current_active_user),
    service: BorrowService = Depends(get_borrow_service),
):
    updated_record = await service.return_book(borrow_record)
    borrow_details = await service.get_borrow_details(updated_record.id)
    return borrow_details


@router.post(
    "/mark-lost/{borrow_id}",
    response_model=BorrowRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark a book as lost",
    tags=["borrowing"],
)
async def mark_borrow_as_lost(
    borrow_id: UUID = Path(..., description="THe ID of the borrow record"),
    user: User = Depends(user_is_librarian_or_admin),
    service: BorrowService = Depends(get_borrow_service),
):
    updated_record = await service.mark_borrow_as_lost(borrow_id)
    borrow_details = await service.get_borrow_details(updated_record.id)
    return borrow_details


@router.get(
    "/history",
    response_model=List[BorrowRecordResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a list of borrows",
    tags=["borrowing"],
)
async def get_borrow_history(
    params: BorrowHistoryFilter = Query(..., description="The filter parameters for the borrows"),
    user: User = Depends(get_current_active_user),
    service: BorrowService = Depends(get_borrow_service),
):
    borrows = await service.get_reader_borrow_history(user.id, params)
    return borrows


@router.get(
    "/users/{user_id}/history",
    response_model=List[BorrowRecordResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a list of borrows for a user",
    tags=["borrowing"],
)
async def get_borrow_history_for_user(
    user_id: UUID = Path(..., description="The ID of the user"),
    params: BorrowHistoryFilter = Query(..., description="The filter parameters for the borrows"),
    user: User = Depends(user_is_librarian_or_admin),
    service: BorrowService = Depends(get_borrow_service),
):
    borrows = await service.get_borrow_history_for_user(user_id, params)
    return borrows


@router.get(
    "/active",
    response_model=List[BorrowRecordResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a list of active borrows",
    tags=["borrowing"],
)
async def get_active_borrows(
    user: User = Depends(get_current_active_user),
    service: BorrowService = Depends(get_borrow_service),
):
    borrows = await service.get_active_borrows_for_reader(user.id)
    return borrows


@router.get(
    "/",
    response_model=List[BorrowRecordResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a list of overdue borrows",
    tags=["borrowing"],
)
async def get_all_borrows(
    params: BorrowHistoryFilter = Query(..., description="The filter parameters for the borrows"),
    user: User = Depends(user_is_librarian_or_admin),
    service: BorrowService = Depends(get_borrow_service),
):
    borrows = await service.get_all_borrows(params)
    return borrows



@router.post(
    "/requests",
    response_model=BookRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request a book",
    tags=["book requests"],
)
async def request_book(
    request_data: BookRequestCreate,
    user: User = Depends(get_current_active_user),
    service: BorrowService = Depends(get_borrow_service),
):
    request = await service.create_request(request_data)
    return request


@router.get(
    "/requests/{request_id}",
    response_model=BookRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a book request by ID",
    tags=["book requests"],
)
async def get_request_by_id(
    request_id: UUID,
    user: User = Depends(get_current_active_user),
    service: BorrowService = Depends(get_borrow_service),
):
    request = await service.get_request_by_id(request_id)
    if user.role != UserRole.LIBRARIAN and user.role != UserRole.ADMIN and request.reader_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own requests",
        )
    return request

@router.get(
    "/requests",
    response_model=List[BookRequestResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a list of book requests",
    tags=["book requests"],
)
async def get_all_requests(
    params: BookRequestFilter = Query(..., description="The filter parameters for the requests"),
    user: User = Depends(get_current_active_user),
    service: BorrowService = Depends(get_borrow_service),
):
    requests = await service.get_all_requests(params)
    return requests