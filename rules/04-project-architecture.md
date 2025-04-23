# Project Architecture

## Current Structure Reference
<!-- Run this to provide fresh structure data: --> 
```bash
tree -L 4 -a -I 'node_modules|-git|_pycache_|.DS_Store|.pytest_cache | - vscode'
```

## Architectural Documentation

```sh
Sales/ (First top folder)
├── App/ (Folder contains:)
│   ├── @AppDelegate.swift (main app life cycle)
│   ├── @Appearance.swift (UIKit appearance helper functions to be applied on the whole app level)
│   ├── @AppSecureStorage.swift (a keychain wrapper to store sensitive user data)
│   ├── @AppSettings.swift (UserDefaults wrapper that is used a helper to store user non sensitive data like app settings or favorites or etc anything like this)
│   ├── GoogleService-Info.plist (google specific file do not touch it)
│   ├── Injection.swift (Dependency Injection helper to manage dependencies for the app, usually you do not need to work on it unless you create new repositories for data access)
│   ├── @SalesApp.swift (@main entry point for the app, and scene configuration)
│   ├── Config/ (sub folder in App folder which contains two files:)
│   │   ├── @AppConfig.swift (to manage app environments like Staging and Production and their related data)
│   │   └── @RemoteConfig.swift (a Firebase RemoteConfig helper to fetch config values remotely from Firebase Console)
│   └── Font/ (second sub folder in App folder)
│       ├── Fonts (folder - contains the fonts used in the app)
│       └── @ScaledFontUI.swift (custom font helper to be used like the default system font styles)
├── Assets.xcassets/ (folder)
│   └── Images and colors (contains images and colors)
├── Data/ (folder contains the following sub folders:)
│   ├── Models/ (data models used in the app)
│   │   └── Data models (this could be @Codable, Codable, regular structs)
│   ├── Local/ (contains:)
│   │   ├── @LocalDataManager.swift (reads data from files in the Bundle)
│   │   └── JsonMocks/ (folder)
│   │       └── Json files (to store all json files needed to make the app run in Mock scheme)
│   ├── Network/ (network related folder contains:)
│   │   ├── Network helpers (network related helper classes)
│   │   └── @AuthorizationManager.swift (manages user fetched credentials)
│   └── Repos/ This folder contains repository classes and structs that manage data fetching to serve the app.
            - You typically won’t need to modify the DataRepoType file.
            - Each repository file usually includes three main parts:
                1. A protocol that defines the repository interface (e.g., HomeRepoType).
                2. An EndPoint extension that provides static functions with names matching those in the protocol.
                3. A repository final class (e.g., `final class UserRepo`) that implements the protocol.
            - This repository class often has two subtypes:
                1. A RemoteDataRepo struct that uses the network manager to fetch data from the endpoint.
                2. A LocalDataRepo struct that fetches data from JSON mock files.
├── Helpers/ (folder contains:)
│   ├── Helper classes and methods (helper classes and methods)
│   ├── @Error.swift (error handling)
│   ├── @Constants.swift (constant types)
│   ├── @Localizable.xcstrings (Localizable strings catalogue to hold English and Arabic translations for strings)
│   ├── Extensions/ (folder)
│   │   └── Extensions folder (extensions over native Swift types to provide additional functionality)
│   └── Text Validators/ (folder)
│       └── Text Validator folder (validates text input in text fields)
├── Views/ (folder contains:)
│   ├── @MainView.swift (the base view that holds other views)
│   ├── @MoreView.swift (contains various other views not shown on the tab bar or side bar in iPad)
│   ├── Common/ (sub folders for:)
│   │   └── Common shared views (cotains views that are shared in more than once view the project)
│   ├── Navigation/ sub folders for:
│   │   ├── @Router.swift (manages views navigation in the app based on SwiftUI NavigationStack)
│   │   ├── @TabBar.swift (holds main views in the app which are @MainView.swift, @BookmarksView.swift, @SalesCalendar.swift and @MoreView.swift in the iPhone app)
│   │   └── @SplitView.swift (holds the main views in the iPad app)
│   └── Views folder/ 
            - Each view has its own folder. A view folder may contain one or more views. 
            - Typically, there is also a view model file that holds the view logic.
            - The view model class should be `final` and adopts the ObservableObject protocol. Import Resolver to define the injected repository property, from which the view fetches its data (if needed), like this:
            `@Injected private var repo: HomeRepoType`
            - The view model file should be named using the {ViewName}VM format, and the class name should match the file name. When you create a view model file, define it as a private property inside the view like this:
            `@StateObject private var vm = HomeVM()`
            - If the view opens another view, create a subfolder under the cotaning view folder. This subfolder should contain the new view’s struct and a separate view model file (if it needs to hold any logic).
└── SalesTests/ (contains:)
    ├── TestPlan (Test Plan)
    └── UnitTests/ (contains:)
        └── Unit tests (various unit tests)
```
