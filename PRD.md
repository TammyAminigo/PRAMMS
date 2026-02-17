# Product Requirements Document (PRD)
## PRAMMS (Property Rental and Maintenance Management System)

### 1. Introduction
PRAMMS is a "Landlord-Centric" web application designed to streamline property management for small-to-medium scale landlords. It facilitates property tracking, tenant onboarding via controlled invitations, and a streamlined maintenance request system.

### 2. Objectives
*   **Centralized Management**: Allow landlords to manage multiple properties and tenants from a single dashboard.
*   **Controlled Access**: Ensure security through a strict "invitation-only" onboarding process for tenants.
*   **Efficient Communication**: Simplify the reporting and tracking of maintenance issues.
*   **Professional UX**: Provide a modern, responsive, and trustworthy user interface inspired by fintech aesthetics (PiggyVest).

### 3. Target Audience
*   **Landlords**: Property owners who need a simple tool to manage their operational workflow.
*   **Tenants**: Renters who need a unified channel to view lease details and report issues.

### 4. Core Features

#### 4.1. Authentication & Authorization
*   **Role-Based Access Control (RBAC)**: Users are strictly categorized as Landlords or Tenants effectively determining their dashboard view and permissions.
*   **Landlord Registration**: Public registration form with required fields (Name, Email, Phone, Gender, Password).
*   **Tenant Onboarding**:
    *   **No Public Registration**: Tenants cannot self-register.
    *   **Invitation System**: Landlords generate unique, time-limited (7-day), single-use UUID links for specific properties.
    *   **Registration**: Tenants participating via invite have their account automatically linked to the landlord and property upon signup.
*   **User Profiles**: Profile management including profile picture upload, phone number, and gender selection.

#### 4.2. Property Management (Landlord)
*   **Add Property**: Landlords can list new properties with details (Name, Address, Rent Amount, Rent Period).
*   **View Properties**: List view of all owned properties with occupancy status.
*   **Edit/Update**: Capability to modify property details.

#### 4.3. Tenant Management
*   **Invite Tenant**: Generate invitation links for specific unoccupied properties.
*   **View Tenants**: Access tenant contact info, move-in dates, and lease duration.
*   **One-Tenant Policy**: System enforces a strict one-tenant-per-property rule to prevent data conflicts.

#### 4.4. Maintenance Request System
*   **Create Request (Tenant)**: Tenants can submit maintenance tickets with:
    *   Title & Description
    *   Priority Level (Low, Medium, High, Emergency)
    *   Images (Up to 3 photos, hosted on Cloudinary)
*   **Manage Request (Tenant)**:
    *   **Edit**: Tenants can modify request details (Title, Description, Priority) while status is 'Pending' or 'In Progress'.
    *   **Photo Management**: Tenants can add or remove photos from existing requests.
*   **Process Request (Landlord)**:
    *   View all requests for their properties.
    *   Update status (Pending -> In Progress -> Completed).
    *   Add "Landlord Notes" for the tenant.

### 5. Technical Specifications

#### 5.1. Tech Stack
*   **Backend**: Django (Python web framework)
*   **Database**: PostgreSQL (Production), SQLite (Local Dev)
*   **Storage**: Cloudinary (Media/Image storage), WhiteNoise (Static file serving)
*   **Deployment**: Railway.app

#### 5.2. Security Requirements
*   **Zero Trust Architecture**: "Never trust, always verify" approach for tenant access.
*   **CSRF Protection**: Standard Django protection for all forms.
*   **Secure Password Storage**: PBKDF2 hashing.
*   **Token Security**: Cryptographically secure UUID v4 for invitations.

### 6. User Interface (UI) / User Experience (UX)
*   **Design Philosophy**: "PiggyVest" inspired aesthetic.
*   **Color Palette**: Deep Navy (`#0a1628`) primary, Vibrant Green (`#00c853`) accent.
*   **Responsive Design**: Mobile-first approach using Flexbox and CSS Grid.
*   **Feedback**: Toast messages for success/error actions (e.g., "Invitation Link Copied", "Request Submitted").

### 7. Future Roadmap (Potential)
*   Rent Payment Integration.
*   Lease Document Generation.
*   Email/SMS Notifications for status updates.
*   Chat System.
