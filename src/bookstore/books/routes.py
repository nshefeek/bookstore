from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, Query, status

from bookstore.auth.models import User
from bookstore.auth.dependencies import user_is_librarian_or_admin

from .models import BookStatus
from .services import BookCategoryService, BookService
from .dependencies import get_category_service, get_book_service
from .schemas import BookCategoryCreate, BookCategoryResponse, BookCategoryUpdate, BookCreate, BookResponse, BookTitleCreate, BookTitleDetailResponse, BookTitleResponse, BookTitleSearchParams, BookTitleSearchResponse, BookTitleUpdate, BookUpdate


router = APIRouter()


@router.post(
    "/categories",
    response_model=BookCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book category",
    tags=["categories"],
)
async def create_category(
    data: BookCategoryCreate,
    user: User = Depends(user_is_librarian_or_admin),
    service: BookCategoryService = Depends(get_category_service),
):
    return await service.create_category(data)


@router.get(
    "/categories",
    response_model=list[BookCategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all book categories",
    tags=["categories"],    
)
async def get_all_categories(
    service: BookCategoryService = Depends(get_category_service),
):
    return await service.get_all_categories()


@router.get(
    "/categories/{category_id}",
    response_model=BookCategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific book category",
    tags=["categories"],
)
async def get_category_by_id(
    category_id: UUID,
    service: BookCategoryService = Depends(get_category_service),
):
    return await service.get_category_by_id(category_id)


@router.put(
    "/categories/{category_id}",
    response_model=BookCategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a specific book category",
    tags=["categories"],
)
async def update_category(
    category_id: UUID,
    data: BookCategoryUpdate,
    user: User = Depends(user_is_librarian_or_admin),
    service: BookCategoryService = Depends(get_category_service),
):
    return await service.update_category(category_id=category_id, category_data=data)


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a specific book category",
    tags=["categories"],
)
async def delete_category(
    category_id: UUID,
    user: User = Depends(user_is_librarian_or_admin),
    service: BookCategoryService = Depends(get_category_service),
):
    return await service.delete_category(category_id)


@router.post(
    "/",
    response_model=BookTitleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book title",
    tags=["books"],
)
async def create_book(
    data: BookTitleCreate,
    user: User = Depends(user_is_librarian_or_admin),
    service: BookService = Depends(get_book_service),
):
    return await service.create_title(data)


@router.get(
    "/",
    response_model=list[BookTitleResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all book titles",
    tags=["books"],
)
async def get_all_titles(
    skip: int = 0,
    limit: int = 100,
    service: BookService = Depends(get_book_service),
):
    return await service.get_all_titles(skip, limit)


@router.get(
    "/{title_id}",
    response_model=BookTitleDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific book title",
    tags=["books"],
)
async def get_title_by_id(
    title_id: UUID,
    include_copies: bool = False,
    service: BookService = Depends(get_book_service),
):
    if include_copies:
        title = await service.get_title_by_id(title_id, include_copies=True)

        if title and title.copies:
            available_copies = sum(1 for copy in title.copies if copy.status == BookStatus.AVAILABLE)
            total_copies = len(title.copies)

        data = BookTitleResponse.model_validate(title)
        data.available_copies = available_copies
        data.total_copies = total_copies

        return data
        
    return await service.get_title_by_id(title_id)


@router.get(
    "/{isbn}",
    response_model=BookTitleDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific title using the ISBN",
    tags=["books"],
)
async def get_title_by_isbn(
    isbn: str,
    include_copies: bool = False,
    service: BookService = Depends(get_book_service)
):
    if include_copies:
        title = await service.get_title_by_isbn(isbn, include_copies)

        if title and title.copies:
            available_copies = sum(1 for copy in title.copies if copy.status == BookStatus.AVAILABLE)
            total_copies = len(title.copies)


        data = BookTitleDetailResponse.model_validate(title)
        data.available_copies = available_copies
        data.total_copies = total_copies

        return data
    
    return await service.get_title_by_isbn(isbn)


@router.get(
    "/search",
    response_model=BookTitleSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search for book title",
    tags=["books"]
)
async def search_titles(
    params: BookTitleSearchParams = Query(),
    service: BookService = Depends(get_book_service),
):
    items = []
    books, total = await service.search_titles(params)

    for book in books:
        if book.copies:
            available_copies = sum(1 for copy in book.copies if copy.status == BookStatus.AVAILABLE)
            total_copies = len(book.copies)
            
        data = BookTitleResponse.model_validate(book)
        data.available_copies = available_copies
        data.total_copies = total_copies
        items.append(data)

    total_pages = (total + params.limit - 1) // params.limit if total > 0 else 0
    return BookTitleSearchResponse(
        items=items,
        total=total,
        page=params.page,
        limit=params.limit,
        pages=total_pages,
    )


@router.put(
    "/{title_id}",
    response_model=BookTitleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a book title",
    tags=["books"]
)
async def update_title(
    title_id: UUID,
    data: BookTitleUpdate,
    user: User = Depends(user_is_librarian_or_admin),
    service: BookService = Depends(get_book_service)
):
    return await service.update_title(title_id, data)


@router.delete(
    "/{title_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book title",
    tags=["books"],
)
async def delete_title(
    title_id: UUID,
    user: User = Depends(user_is_librarian_or_admin),
    service: BookService = Depends(get_book_service)
):
    return await service.delete_title(title_id)


@router.post(
    "/copies",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a book copy of a title",
    tags=["book copies"]
)
async def add_book(
    data: BookCreate,
    user: User = Depends(user_is_librarian_or_admin),
    service: BookService = Depends(get_book_service)
):
    copy = await service.create_book(data)
    return copy


@router.get(
    "/{title_id}/copies",
    response_model=List[BookResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all copies under a title",
    tags=["book copies"]
)
async def get_all_copies_of_title(
    title_id: UUID,
    availability: bool = Query(False, description="Filter for available copies only"),
    service: BookService = Depends(get_book_service)
):
    if availability:
        copies = await service.get_all_available_books_for_title(title_id)
    else:
        copies = await service.get_all_books_for_title(title_id)
    return copies


@router.get(
    "/copies/{book_id}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a book copy of a title by ID",
    tags=["book copies"]
)
async def get_copy_by_id(
    book_id: UUID,
    service: BookService = Depends(get_book_service)
):
    copy = await service.get_book_by_id(book_id)
    return copy


@router.get(
    "/copies/{barcode}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a book copy of a title by barcode",
    tags=["book copies"]
)
async def get_copy_by_barcode(
    barcode: str,
    service: BookService = Depends(get_book_service)
):
    copy = await service.get_book_by_barcode(barcode)
    return copy


@router.put(
    "/copies/{book_id}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a book under a title",
    tags=["book copies"]
)
async def update_copy(
    book_id: UUID,
    data: BookUpdate,
    user: User = Depends(user_is_librarian_or_admin),
    service: BookService = Depends(get_book_service)
):
    copy = await service.update_book(book_id, data)
    return copy


@router.delete(
    "/copies/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book copy under a title by ID",
    tags=["book copies"]
)
async def delete_book_by_id(
    book_id: UUID,
    user: User = Depends(user_is_librarian_or_admin),
    service: BookService = Depends(get_book_service)
):
    return await service.delete_book(book_id)


@router.patch(
    "/copies/{book_id}/status",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Update the availability status of a book copy",
    tags=["book copies"]
)
async def update_book_status(
    book_id: UUID,
    book_status: BookStatus,
    user: User = Depends(user_is_librarian_or_admin),
    service: BookService = Depends(get_book_service)
):
    copy = await service.update_book_status(book_id, book_status)
    return copy