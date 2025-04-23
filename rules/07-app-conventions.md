# App Conventions

## Error Handling
- Use the structured error types in Error.swift file in the Helpers folder for predictable error cases, add to them if necessary.
- Show user-friendly error messages and allow graceful recovery where possible.  
- Log errors for debugging and maintenance.  
- Avoid silently failing, surface issues in a manageable way.
- DO NOT JUMP TO CONCLUSIONS! Consider multiple possible causes for the before deciding.
- Explain the problem in plain English.
- Make minimal necessary changes, changing as few lines of code as possible.
- In case of strange errors, ask the user to perform a Perplexity web search to find the latest up-to-date information.


## Fonts
- Use only the custom fonts in the Font folder.
- Use `.scaledFont` and `.customFont` modifiers to apply the fonts.
- Use the `.scaledFont` modifier with the pre-defined text styles defined in the ScaledFontUI.swift file exactly at the extension: ScaledFont.StyleKey, the font name and size for each text style is defined in the Font -> CustomFontStyles.swift file.
- If the font size you want to apply is not within the pre-defined text styles, then apply the .customFont modifier with the font name parameter taken from the FontName enum in the ScaledFontUI.swift file and an explicit size parameter.

## Colors
- Use only the colors defined in the Assets.xcassets folder, for example you can use the `p500` color like this `Color.p500` or implicitly like this `.p500` where it does not produce linter errors.
- Apply gradients where you find it appealing to the user.
- Every color in the Assets.xcassets folder has two variants for light and dark mode, so dark mode is supported out of the box.
- Use `.background(.bgPrimary)` as the background color for the views.

## Localizable Text
- Avoid writing Arabic text directly in a Text view or any SwiftUI view that renders text.
- Instead, use the English version of the text in the Text view (or any SwiftUI view that accepts a LocalizedStringKey parameter), and add that English text to the @Localizable.xcstrings file.
- Provide the Arabic translation under the "ar" key and the English version under the "en" key, follow the example to add a translation entry.
- Example for adding the "bookmarks" entry in the @Localizable.xcstrings:

```json
"bookmarks" : {
      "extractionState" : "manual",
      "localizations" : {
        "ar" : {
          "stringUnit" : {
            "state" : "translated",
            "value" : "المحفوظات"
          }
        },
        "en" : {
          "stringUnit" : {
            "state" : "translated",
            "value" : "Bookmarks"
          }
        }
      }
    }
```
- For non-SwiftUI contexts (or views that don’t support LocalizedStringKey), use the `.localized` extension on String to retrieve the localized value.

## SwiftUI Previews
- Use `#Preview` macro to create previews for the views instead of using `PreviewProvider` and static var previews variable.
- Use `@Previewable` macro before any `@State`, `@StateObject`, `@Environment` variables.
- Use `.injectValuesForPreview()` modifier to inject the values for the previews.
