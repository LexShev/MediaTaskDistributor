# Oplan3 Extension: Broadcast Material Management System

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![MSSQL](https://img.shields.io/badge/Microsoft%20SQL%20Server-CC2927?style=for-the-badge&logo=microsoft%20sql%20server&logoColor=white)
![NGINX](https://img.shields.io/badge/NGINX-009639?style=for-the-badge&logo=nginx&logoColor=white)

A Django-based web application that extends the functionality of Oplan3 broadcast scheduling system by providing comprehensive material management and workforce distribution tools.

## Key Features

### Material Management
- Filters unverified/unreviewed content from broadcast schedules
- Creates task queues organized by days
- Maintains a complete database of all materials available for assignment
- Batch completion for serial content to avoid duplicate entries

### Workforce Distribution
- **Automatic task assignment** based on employee KPI metrics
- Balanced workload distribution among team members
- Manager dashboard with productivity analytics
- Employee schedule tracking (workdays, vacations, time off)

### Workflow Tools
- **Integrated video streaming** via NGINX server
- Direct access to original video files for editing (Adobe Premiere Pro, DaVinci Resolve)
- Advanced search module for quick database queries
- Comprehensive logging of all file operations
- Automated reporting on completed work

### Specialized Modules
- **Broadcast Engineer Dashboard**: Tracks material readiness by date
- **Overachievement Module**: Additional material pool for periods with exceeded targets
- **Admin Panel**: Full oversight of team performance and operations

## Technical Overview

### System Architecture
- **Backend**: Django (Python)
- **Database**: Microsoft SQL Server (MSSQL) - direct integration with Oplan3
- **Streaming**: NGINX video streaming server
- **Frontend**: Django templates with responsive design

### Integration Points
- Seamless connection to existing Oplan3 MSSQL database
- Uses `pyodbc` for database connectivity
- Maintains data consistency with the primary scheduling system
- Read-only access to broadcast schedules with write-back for verification status
