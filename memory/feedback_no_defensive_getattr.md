---
name: Don't use defensive getattr on typed models
description: Access Pydantic/dataclass fields directly instead of wrapping in getattr with fallback defaults
type: feedback
---

Don't use `getattr(obj, 'field', default)` when the object is a Pydantic model or dataclass that guarantees the field exists.

**Why:** It's unnecessary defensive code that obscures the actual type contract. If a model defines `field: bool = False`, the field is always present — `getattr` with a fallback adds noise and implies uncertainty that doesn't exist.

**How to apply:** When reading attributes from typed models (Pydantic, dataclass, TypedDict), just use `obj.field` directly. Only use `getattr` with a fallback when the attribute genuinely might not exist (e.g., duck-typed objects, optional mixins).
