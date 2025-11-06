"""Product management API endpoints.

This module provides REST API endpoints for product management:
- POST /api/products - Create new product
- GET /api/products - List all products (with optional filtering)
- GET /api/products/{id} - Get product by ID
- PUT /api/products/{id} - Update product
- PUT /api/products/{id}/price - Update product price only
- DELETE /api/products/{id} - Delete product
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.product_service import (
    ProductService,
    CreateProductData,
    SetItemData,
)
from app.schemas.product import (
    CreateProductRequest,
    UpdateProductRequest,
    UpdatePriceRequest,
    ProductResponse,
    DeleteProductResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/api/products", tags=["products"])


def get_product_service() -> ProductService:
    """Dependency to get ProductService instance.

    Returns:
        ProductService instance
    """
    return ProductService()


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def create_product(
    request: CreateProductRequest,
    db: Session = Depends(get_db),
    product_service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Create a new product.

    Args:
        request: Product creation request data
        db: Database session
        product_service: Product service instance

    Returns:
        Created product data

    Raises:
        HTTPException 400: If validation fails or set product without set_items
        HTTPException 409: If product name already exists
    """
    # Validate set product requirements
    if request.product_type == "set":
        if not request.set_items or len(request.set_items) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_SET_ITEMS",
                    "message": "セット商品には1つ以上の構成単品を指定する必要があります",
                },
            )

    # Convert request to service data
    set_items_data = None
    if request.set_items:
        set_items_data = [
            SetItemData(
                product_id=item.product_id,
                quantity=item.quantity,
            )
            for item in request.set_items
        ]

    create_data = CreateProductData(
        name=request.name,
        unit_cost=request.unit_cost,
        sale_price=request.sale_price,
        initial_stock=request.initial_stock,
        product_type=request.product_type,
        set_items=set_items_data,
    )

    try:
        product = product_service.create_product(create_data, db)
        return ProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
            },
        )


@router.get(
    "",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
)
def get_all_products(
    product_type: Optional[str] = None,
    db: Session = Depends(get_db),
    product_service: ProductService = Depends(get_product_service),
) -> List[ProductResponse]:
    """Get all products, optionally filtered by type.

    Args:
        product_type: Optional product type filter ('single' or 'set')
        db: Database session
        product_service: Product service instance

    Returns:
        List of products
    """
    products = product_service.get_all_products(db, product_type=product_type)
    return [ProductResponse.model_validate(p) for p in products]


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse},
    },
)
def get_product_by_id(
    product_id: UUID,
    db: Session = Depends(get_db),
    product_service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Get product by ID.

    Args:
        product_id: Product UUID
        db: Database session
        product_service: Product service instance

    Returns:
        Product data

    Raises:
        HTTPException 404: If product not found
    """
    product = product_service.get_product_by_id(product_id, db)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "RESOURCE_NOT_FOUND",
                "message": "指定された商品が見つかりません",
                "details": {
                    "resource_type": "product",
                    "resource_id": str(product_id),
                },
            },
        )

    return ProductResponse.model_validate(product)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def update_product(
    product_id: UUID,
    request: UpdateProductRequest,
    db: Session = Depends(get_db),
    product_service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Update product attributes.

    Args:
        product_id: Product UUID
        request: Product update request data
        db: Database session
        product_service: Product service instance

    Returns:
        Updated product data

    Raises:
        HTTPException 404: If product not found
        HTTPException 400: If validation fails
    """
    # Convert request to dict, excluding None values
    updates = request.model_dump(exclude_none=True)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "少なくとも1つのフィールドを指定してください",
            },
        )

    product = product_service.update_product(product_id, updates, db)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "RESOURCE_NOT_FOUND",
                "message": "指定された商品が見つかりません",
                "details": {
                    "resource_type": "product",
                    "resource_id": str(product_id),
                },
            },
        )

    return ProductResponse.model_validate(product)


@router.put(
    "/{product_id}/price",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def update_price(
    product_id: UUID,
    request: UpdatePriceRequest,
    db: Session = Depends(get_db),
    product_service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Update product price only.

    This endpoint specifically handles price changes, maintaining
    historical price integrity for past sales records.

    Args:
        product_id: Product UUID
        request: Price update request data
        db: Database session
        product_service: Product service instance

    Returns:
        Updated product data

    Raises:
        HTTPException 404: If product not found
        HTTPException 400: If validation fails
    """
    try:
        product = product_service.update_price(
            product_id,
            request.sale_price,
            db,
        )
        return ProductResponse.model_validate(product)
    except ValueError as e:
        # Product not found
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "RESOURCE_NOT_FOUND",
                    "message": str(e),
                },
            )
        # Other validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
            },
        )


@router.delete(
    "/{product_id}",
    response_model=DeleteProductResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse},
    },
)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    product_service: ProductService = Depends(get_product_service),
) -> DeleteProductResponse:
    """Delete a product.

    Args:
        product_id: Product UUID
        db: Database session
        product_service: Product service instance

    Returns:
        Deletion result

    Raises:
        HTTPException 404: If product not found
    """
    success = product_service.delete_product(product_id, db)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "RESOURCE_NOT_FOUND",
                "message": "指定された商品が見つかりません",
                "details": {
                    "resource_type": "product",
                    "resource_id": str(product_id),
                },
            },
        )

    return DeleteProductResponse(
        success=True,
        message="商品が正常に削除されました"
    )
