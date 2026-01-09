# PRAMMS Technical Implementation Summary

## 1. System Architecture & Design Pattern

### 1.1 Django MVT (Model-View-Template) Pattern

PRAMMS is built using Django's **Model-View-Template (MVT)** architectural pattern, which is particularly well-suited for this "Landlord-Centric" application for the following reasons:

| Component | Role in PRAMMS |
|-----------|----------------|
| **Model** | Defines data structure (User, Property, TenantProfile, MaintenanceRequest) with business logic constraints |
| **View** | Handles request processing, access control, and business logic (role verification, invitation validation) |
| **Template** | Renders role-specific dashboards and forms with consistent UI |

**Why MVT for Landlord-Centric Design:**
- **Separation of Concerns**: Landlords and tenants share the same codebase but see entirely different views
- **Rapid Development**: Django's ORM allowed quick implementation of complex relationships (Landlord → Property → Tenant)
- **Built-in Security**: CSRF protection, secure password hashing, and session management out-of-the-box

### 1.2 Role-Based Access Control (RBAC) Implementation

RBAC is implemented through a **custom User model** with role properties and **view-level enforcement**:

```python
# accounts/models.py
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('landlord', 'Landlord'),
        ('tenant', 'Tenant'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='landlord')
    
    @property
    def is_landlord(self):
        return self.role == 'landlord'
    
    @property
    def is_tenant(self):
        return self.role == 'tenant'
```

**View-Level Enforcement Pattern:**
```python
# maintenance/views.py
@login_required
def maintenance_create(request):
    if not request.user.is_tenant:
        messages.error(request, 'Only tenants can create maintenance requests.')
        return redirect('dashboard')
    # ... tenant-only logic
```

**Dashboard Routing Logic:**
```python
# accounts/views.py
@login_required
def dashboard(request):
    if request.user.is_landlord:
        return redirect('landlord_dashboard')
    elif request.user.is_tenant:
        return redirect('tenant_dashboard')
```

---

## 2. Database Logic & Relationships

### 2.1 Entity Relationship Model

```
┌─────────────┐       ┌──────────────┐       ┌──────────────────┐
│    User     │  1:N  │   Property   │  1:1  │  TenantProfile   │
│ (Landlord)  │──────▶│              │◀──────│                  │
└─────────────┘       └──────────────┘       └──────────────────┘
      │                      │                       │
      │                      │                       │
      │                      ▼                       │
      │               ┌──────────────┐               │
      │               │InvitationLink│               │
      │               └──────────────┘               │
      │                                              │
      └──────────────────────────────────────────────┘
                        (landlord FK)
```

### 2.2 Key Relationship Definitions

```python
# properties/models.py

class Property(models.Model):
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='properties'
    )
    # Landlord can own multiple properties (1:N)
    # CASCADE: If landlord deleted, all properties deleted

class TenantProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenant_profile'
    )
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenants'
    )
    rental_property = models.OneToOneField(
        Property,
        on_delete=models.CASCADE,
        related_name='tenant'
    )
```

### 2.3 Constraint Logic: Tenant Cannot Exist Without Property/Landlord

The system enforces that **a Tenant cannot exist without a valid Property and Landlord link** through:

1. **Database-Level Constraints:**
   - `TenantProfile.landlord` is a **required ForeignKey** (no `null=True`)
   - `TenantProfile.rental_property` is a **required OneToOneField**
   - Both use `on_delete=models.CASCADE` - deleting landlord/property removes tenant

2. **Application-Level Enforcement:**
   - Tenants can ONLY be created through the invitation flow
   - No standalone tenant registration form exists
   - The `accept_invitation` view creates User and TenantProfile atomically

3. **OneToOne Constraint:**
   - `rental_property = models.OneToOneField(Property, ...)` ensures one tenant per property
   - Attempting to assign two tenants to one property raises `IntegrityError`

---

## 3. Key Algorithms: The Invitation Flow

### 3.1 Single-Use Invitation Link Architecture

The invitation system uses a **cryptographically secure UUID token** with time-based expiration:

```python
# properties/models.py
class InvitationLink(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    def is_valid_invite(self):
        """Check if the invitation link is still valid."""
        return not self.is_used and timezone.now() < self.expires_at
```

### 3.2 UUID Generation

```python
import uuid

# Django uses uuid.uuid4() which generates a random 128-bit UUID
# Format: 8-4-4-4-12 hexadecimal characters
# Example: 550e8400-e29b-41d4-a716-446655440000

token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
```

**Security Properties:**
- **Cryptographically random**: 2^122 possible values (collision probability negligible)
- **Non-sequential**: Cannot guess next/previous tokens
- **Unique constraint**: Duplicate tokens rejected at database level

### 3.3 Invitation Expiration & Invalidation Logic

```python
# properties/views.py - accept_invitation view
def accept_invitation(request, token):
    invitation = get_object_or_404(InvitationLink, token=token)
    
    # STEP 1: Validate invitation
    if not invitation.is_valid_invite():
        messages.error(request, 'This invitation link has expired or already been used.')
        return redirect('home')
    
    if request.method == 'POST':
        form = TenantRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # STEP 2: Create tenant profile (atomic operation)
            TenantProfile.objects.create(
                user=user,
                landlord=invitation.landlord,
                rental_property=invitation.rental_property,
                move_in_date=form.cleaned_data['move_in_date']
            )
            
            # STEP 3: Invalidate invitation (single-use enforcement)
            invitation.rental_property.is_occupied = True
            invitation.rental_property.save()
            invitation.is_used = True  # <-- Mark as used
            invitation.save()
            
            login(request, user)
            return redirect('tenant_dashboard')
```

**Flow Diagram:**
```
Landlord creates invitation → UUID generated → Link shared
                                    ↓
Tenant clicks link → is_valid_invite() checked
                                    ↓
                    ┌───────────────┴───────────────┐
                    │                               │
              Valid                            Invalid
                    ↓                               ↓
         Show registration form            Show error message
                    ↓
         Submit form → Create User + TenantProfile
                    ↓
         Set is_used=True, is_occupied=True
                    ↓
         Auto-login tenant → Dashboard
```

---

## 4. UI/UX Design Philosophy

### 4.1 "PiggyVest Vibe" - Design Token Approach

The design draws inspiration from PiggyVest's fintech aesthetic using CSS Custom Properties:

```css
/* static/css/style.css */
:root {
    /* Primary Colors - Deep Navy (PiggyVest-inspired dark theme) */
    --primary-dark: #0a1628;
    --primary: #1a1f3c;
    --primary-light: #2d3561;

    /* Accent Colors - Vibrant Green (trust/financial stability) */
    --accent: #00c853;
    --accent-light: #4caf50;
    --accent-dark: #00a043;

    /* Shadows for depth */
    --shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    
    /* Rounded corners for modern feel */
    --radius: 10px;
    --radius-lg: 16px;
}
```

### 4.2 Key CSS Techniques

**Flexbox for Card Layouts:**
```css
.dashboard-stats {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
}

.stat-card {
    flex: 1;
    min-width: 200px;
    background: var(--white);
    border-radius: var(--radius);
    padding: 1.5rem;
}
```

**Responsive Navigation:**
```css
@media (max-width: 768px) {
    .nav-links {
        display: none;
        flex-direction: column;
    }
    
    .mobile-menu-toggle {
        display: block;
    }
}
```

**Status Badges with Semantic Colors:**
```css
.badge-success { background: var(--success); }  /* Green - Completed */
.badge-warning { background: var(--warning); }  /* Yellow - Pending */
.badge-danger { background: var(--danger); }    /* Red - Emergency */
.badge-info { background: var(--info); }        /* Blue - In Progress */
```

---

## 5. Deployment & Challenges

### 5.1 SQLite to PostgreSQL Migration

| Aspect | Local (SQLite) | Production (Railway + PostgreSQL) |
|--------|----------------|-----------------------------------|
| Database | File-based `db.sqlite3` | Cloud-hosted PostgreSQL |
| Config | Hardcoded in settings | Environment variable `DATABASE_URL` |
| Connection | Direct file access | TCP connection with pooling |

**Dynamic Database Configuration:**
```python
# prmms/settings.py
import dj_database_url

if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

### 5.2 WhiteNoise for Static Files

Railway's filesystem is ephemeral, so Django's `collectstatic` approach doesn't work reliably. We used WhiteNoise with `USE_FINDERS`:

```python
WHITENOISE_USE_FINDERS = True  # Serve directly from static/ folder
WHITENOISE_AUTOREFRESH = True  # Auto-detect file changes
```

**Why WhiteNoise:**
- Eliminates need for `collectstatic` during build
- Compresses and caches static files
- Works seamlessly with Gunicorn

### 5.3 Production Bugs & Lessons Learned

| Bug | Root Cause | Fix | Lesson |
|-----|------------|-----|--------|
| `ModuleNotFoundError: dateutil` | Missing from requirements.txt | Added `python-dateutil>=2.8.0` | Always test with fresh virtual environment |
| `TemplateSyntaxError: Invalid block tag` | Template tags split across lines | Put `{% if %}...{% endif %}` on single lines | Django template parser is line-sensitive |
| CSS not loading (404) | Deprecated `DEFAULT_FILE_STORAGE` | Used Django 4.2+ `STORAGES` dictionary | Check Django version migration guides |
| Images broken (404) | Railway ephemeral filesystem | Integrated Cloudinary for media | Stateless deployments need external storage |
| Database connection failed during build | Migrations ran before DB connected | Moved migrate to start command, not build | Understand build vs. runtime phases |

### 5.4 Production Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Railway Platform                        │
│  ┌───────────────┐    ┌───────────────┐    ┌─────────────┐ │
│  │  Web Service  │────│  PostgreSQL   │    │  Cloudinary │ │
│  │  (Gunicorn)   │    │   Database    │    │  (Media)    │ │
│  └───────────────┘    └───────────────┘    └─────────────┘ │
│         │                                          ▲        │
│         │  WhiteNoise                              │        │
│         │  (Static Files)                          │        │
│         ▼                                          │        │
│  ┌───────────────┐                                 │        │
│  │    Django     │─────────────────────────────────┘        │
│  │  Application  │                                          │
│  └───────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Django Models | 6 (User, Property, TenantProfile, InvitationLink, MaintenanceRequest, MaintenanceImage) |
| Views Implemented | 15+ |
| Template Files | 20+ |
| CSS Lines | ~1,300 |
| Production Dependencies | 10 packages |
| Deployment Platform | Railway.app |

---

*Generated for PRAMMS Academic Project Report - January 2026*
