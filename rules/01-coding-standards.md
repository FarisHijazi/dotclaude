# Coding Standards

## Code Quality Fundamentals
- HIGH PRIORITY: ALWAYS Write clean, simple, readable and modular SwiftUI code using latest standards (Swift 6.1+/SwiftUI 6+ as of Dec 2024)
- Prioritize clarity over cleverness - implement features in simplest viable way
- Ensure components maintain a single responsibility with well-defined boundaries within a modular architecture.
- Keep files focused (<250 lines) with clear, consistent naming.
- HIGH PRIORITY: Break down SwiftUI views into smaller, logical subviews for better readability and maintainability:
  - Create subviews within the parent view file when logical boundaries exist, regardless of file length.
  - Choose appropriate subview implementation based on complexity:
    - For simple views: Use computed properties (`var subView: some View { ... }`) or functions (`func subView() -> some View { ... }`).
    - For complex views: Create a separate struct (`struct SubViewName: View { ... }`).
  - When parent view file exceeds 250 lines:
    - Move some subviews to their own files.
    - Name these files as: `ParentView+SubViewName.swift`.
    - Structure the file as extension to parent view: `extension ParentViewName { ... }`.
  - Prioritize moving complex, self-contained subviews to separate files first.

## Execution Standards
- Ensure fully functional, secure, bug-free implementations
- Combine best practices with Apple Human Interface Guidelines
- Use modern Swift features (value types, async/await, declarative patterns)
- Validate requirements understanding before coding

## Code Style & Logging
- Follow Swift naming conventions and structure.
- Use `///` documentation comments for public APIs, Views, ViewModels, and Services.
- Inject dependencies rather than hardcoding them.
- Use the OSLog helpers in Logging.swift for consistent error and event logging.
- New file header requirement:
     ```swift
     //
     //  [FileName].swift
     //  [Project Name]
     //
     //  Created by Murad Jamal on [DD/MM/YYYY].
     //
     ```
     - Replace placeholders with:
       - `[FileName]`: Actual Swift file name matching struct/class
       - `[Project Name]`: Always "Sales" 
       - `[DD/MM/YYYY]`: Current date in day/month/year format
     - Example Implementation:
       ```swift
       //
       //  SalesCalendar.swift
       //  Sales
       //
       //  Created by Murad Jamal on 23/12/2023.
       //
       ```

## Comments
- HIGH PRIORITY: ALWAYS write clear, helpful, and explanatory comments.
- NEVER delete old comments - unless they are obviously wrong or obsolete.
- Document all changes and their reasoning IN THE COMMENTS YOU WRITE.      
- When writing comments, use clear and easy-to-understand language, write in short sentences.
