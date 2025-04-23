# SwiftUI UI UX

## UI Components
- Use `ScrollView` with `.scrollTargetBehavior()` for a better scrolling experience, for more details see [Apple's ScrollView Documentation](https://developer.apple.com/documentation/swiftui/scroll-views).
- Employ `.contentMargins()` for consistent internal spacing.
- Apply `.containerShape()` to customize hit testing areas.
- Use SF Symbols 6 to for local icons, - For more details, see [Apple's SF Symbols Guidelines](https://developer.apple.com/design/human-interface-guidelines/sf-symbols).
- Extract reusable functionality into custom `ViewModifiers`.
- For button styling:
  - Use the two-part initializer: `Button { action } label: { content }` for clear separation of concerns.
  - Apply styling through the `.buttonStyle()` modifier rather than directly styling the label.
  - Create custom button styles using: `struct CustomStyle: ButtonStyle { func makeBody(configuration: Configuration) -> some View { ... } }` when default styles are insufficient.
  - Reuse custom button styles across the app for consistency.
  - Consider extracting frequently used button styles to a dedicated ButtonStyles.swift file in the Common folder.

## Interaction & Animation
- Trigger visual changes with `.animation(value:)`.
- Use Phase Animations for more complex transitions.
- Leverage `.symbolEffect()` for SF Symbol animations.
- Include `.sensoryFeedback()` for haptic or audio cues.
- Utilize SwiftUI gesture system for touch interactions.
- For more details about animations, see [Apple's Animation Documentation](https://developer.apple.com/documentation/swiftui/animations).
- For more details about gestures, see [Apple's Gestures Documentation](https://developer.apple.com/documentation/swiftui/gestures).
- For more details about transitions, see [Apple's Transition Documentation](https://developer.apple.com/documentation/swiftui/transition).

## Accessibility
- Every UI element must have an appropriate `.accessibilityLabel()`, `.accessibilityHint()`, and traits.
- Support VoiceOver by making sure views are `.accessibilityElement()` where needed.
- Ensure and test Dynamic Type support in all text and layouts, verifying with larger text sizes.
- Provide clear, descriptive accessibility text for all elements.
- Respect reduced motion settings and provide alternatives if needed.
