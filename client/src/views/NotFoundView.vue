<template>
  <div class="container py-5 text-center">
    <p class="display-1 fw-semibold text-brand mb-0">404</p>
    <h1 class="h4 page-title mb-3">We could not find that page</h1>
    <p class="text-muted mb-4">
      The link may be out of date, or the page may have moved.
    </p>
    <div class="d-flex gap-2 justify-content-center">
      <RouterLink class="btn btn-primary" to="/">Go home</RouterLink>
      <RouterLink class="btn btn-outline-secondary" to="/shop">Browse the shop</RouterLink>
    </div>
  </div>
</template>
