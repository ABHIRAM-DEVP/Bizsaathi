# T-311: Shareable public customer chat

- **PHASE:** 2  **PRIORITY:** P1
- **OBJECTIVE:** Let sellers share a working public chat page with customers, including alongside a reviewed post and product image.
- **FILES:** `backend/app/routers/businesses.py`, `backend/app/schemas/businesses.py`, `frontend/app/store/`, `frontend/app/posts/page.tsx`
- **DEPENDS ON:** T-308
- **ACCEPTANCE:**
  - An owner can obtain their tenant-scoped public store slug.
  - A public `/store/{slug}` page loads public catalog information and can create or resume a catalog-grounded conversation after customer account sign-in.
  - The share-widget action creates a URL using the current frontend origin, so local and deployed links point to the matching app host.
  - Forwarding a reviewed post with its image includes the public chat URL in both share text and URL payload.
  - Configured browser origins can use the customer account's HttpOnly cookie; no public chat session token is returned and no external publishing is performed.
- **TEST COMMAND:** Backend business/chat endpoint tests; frontend lint, typecheck, and production build.
- **SECURITY:** Public routes expose only public store data; authenticated chat history is account- and store-scoped; the account cookie is opaque, HttpOnly, and revocable; business profile requires owner authorization.
- **OUT OF SCOPE:** External social posting, embedding scripts, and customer PII collection.
- **STATUS:** Implemented; chat integration and frontend production build passed.
