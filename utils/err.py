from fastapi import HTTPException, status


credentials_exception = HTTPException(
  status_code=status.HTTP_401_UNAUTHORIZED,
  detail="Could not validate credentials",
  headers={"WWW-Authenticate": "Bearer"},
)

username_too_long_exception = HTTPException(
  status_code=status.HTTP_400_BAD_REQUEST,
  detail="Username too long.",
)

username_too_short_exception = HTTPException(
  status_code=status.HTTP_400_BAD_REQUEST,
  detail="Username too short.",
)

username_occupied = HTTPException(
  status_code=status.HTTP_409_CONFLICT,
  detail="Username already exists.",
)

internal_error = HTTPException(
  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
  detail="Task failed successfully",
)
