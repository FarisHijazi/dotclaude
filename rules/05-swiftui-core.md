# SwiftUI Core

## State Management
- Use `ObservableObject` for reference types (typically view models holding business logic and app state).
- Use `@Published` properties within @Observable classes so SwiftUI views can bind directly to them.
- Use `@StateObject` for view model observation.
- Pass dependencies via initializers rather than as global singletons.
- Use `@Environment` for app-wide or large-scope states.
- Use `@EnvironmentObject` in the child view to listen for an observable object dependency passsed from the parent view (by `.environmentObject` modifier) to its child view.
- `@State` is only for view-local state.

## Modern Navigation
- Use `NavigationStack` with type-safe navigation.
- Use `Router` class to define views to navigate to.
- DO NOT use `NavigationView` and `NavigationLink`.
- DO NOT create `NavigationStack` inside another `NavigationStack` stack, for example: the HomeView is inside a navigation stack defined in TabBar.swift, you should not create another `NavigationStack` inside any view pushed on HomeView

## Layout System
- Use `Grid` for complex, flexible layouts.
- Use `ViewThatFits` for adaptive interfaces.
- Custom layouts via the `Layout` protocol.
- Apply `containerRelativeFrame()` for responsive sizing and positioning.
- HIGH PRIORITY: Always use traling and leading anchors for the views but not right and left anchors.

## Data & Performance
- Use Swift Data (`@Query`) for direct data fetching and persistence.
- Annotate UI-updating code paths with `@MainActor`.
- Use `TaskGroup` for concurrent operations.
- Implement lazy loading (`LazyVStack`, `LazyHGrid`, `LazyVGrid`, `LazyHStack`) with stable, identifiable items to boost performance.
- When you call an async method when view opens, do not use use the `Task` inside the `.onAppear` modifier, instead use `.task` modifier to call the async method inside it.
