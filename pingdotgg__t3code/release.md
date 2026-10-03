tag: v0.0.45
name: T3 Code v0.0.45
published_at: 2026-10-02T18:17:31Z
prerelease: False

## What's Changed
* fix(shared): merge OpenCode Go limits by credential by @Yash-Singh1 in https://github.com/pingdotgg/t3code/pull/14209
* feat(codex): regenerate protocol bindings for Codex 0.159 by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/14311
* test(server): stop pinning codex install advisory to a release range by @maria-rcks in https://github.com/pingdotgg/t3code/pull/14323
* chore: stop CodeRabbit from editing PR descriptions by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14307
* fix(web): unresolved pull request links use the compact link tooltip by @flamboh in https://github.com/pingdotgg/t3code/pull/14243
* fix(client-runtime): keep model ids in inline code from becoming file chips by @otavio in https://github.com/pingdotgg/t3code/pull/13909
* fix(web): show the agent's question on user-input timeline rows by @saphid in https://github.com/pingdotgg/t3code/pull/12900
* fix(web): open workspace root links in the file explorer by @saphid in https://github.com/pingdotgg/t3code/pull/12449
* fix(grok): recover from crashed provider sessions by @saphid in https://github.com/pingdotgg/t3code/pull/10607
* fix(web): let command menu descriptions use the full row width by @jakaskerjanc in https://github.com/pingdotgg/t3code/pull/8865
* fix(web): multi-PR badges open the linked pull requests panel by @flamboh in https://github.com/pingdotgg/t3code/pull/13211
* fix(web): stop clipping the bottoms of diff file names by @shivamhwp in https://github.com/pingdotgg/t3code/pull/14375
* fix(web): name the step that registers a mobile client by @Sethmr in https://github.com/pingdotgg/t3code/pull/10963
* test(desktop): Keep WSL busy-runtime fixtures visible when sh is bash by @mwolson in https://github.com/pingdotgg/t3code/pull/14351
* chore: bump vite-plus to 1.0 by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/14462
* fix(web): show double bolts for Codex Ultrafast by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14479
* docs: define contribution triage policy by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/14480
* docs: use explicit contribution triage exemptions by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/14485
* fix(server): Grok CLIs older than 1.0.13 are marked broken by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/14486
* fix(clients): hide disconnected environments when adding projects by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/14490
* feat: start threads without a project by @t3dotgg in https://github.com/pingdotgg/t3code/pull/13612
* fix(server): Claude /compact no longer ends early and leaves the thread busy by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14497
* fix(web): Dark+ and Light+ themes import instead of colliding with built-in ids by @flamboh in https://github.com/pingdotgg/t3code/pull/14499
* fix(web): make composer suggestions usable with screen readers by @akj in https://github.com/pingdotgg/t3code/pull/10154
* perf(release): build and publish npm platform packages concurrently by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14028
* perf(ci): run PR checks side by side and balance server shards by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14025
* perf(release): trim Windows packaging setup by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14037
* perf(release): start Windows builds without waiting for the Linux job by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14027
* perf(release): build Vercel deployments early and go live after publish by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14029
* fix(server): Claude subagents with their own model no longer show the parent's model by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14540
* feat(web): restart the agent session from cmd+k to load new skills and plugins by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14542
* fix(web): hotkey settings record plain keys and Tab by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14548
* fix(release): Windows CLI smoke test no longer fails on temp dir cleanup by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14553
* feat: start a new project from just a name by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14527
* fix(desktop): agent clicks in the browser no longer pop Save dialogs by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14573
* chore(mobile): upgrade to Expo SDK 58 and React Native 0.88 RC by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/12045
* feat(mobile): render the Android subscription widget with expo-widgets by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/12046
* feat(mobile): degrade the agent Live Activity once its content goes stale by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/12047
* feat(notifications): stack agent alerts by thread on both platforms by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/12048
* chore(mobile): drive dev-menu suppression from the dev-client launch URL by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/12049
* fix(mobile): read display scale and width from the view's scene, not UIScreen.main by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/12050
* refactor(mobile): adopt Expo Modules 2.0 for function-only native members by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/12051
* feat(mobile): suppress only the on-screen thread's alert on Android by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/12052
* feat(marketing): replace the screenshot crop with a designed social card by @flamboh in https://github.com/pingdotgg/t3code/pull/13487
* docs: update user count in AGENTS.md by @Kamkmgamer in https://github.com/pingdotgg/t3code/pull/11413
* test(web): remove duplicate sidebar ordering tests by @t3-code[bot] in https://github.com/pingdotgg/t3code/pull/14558
* fix: cloned projects show their favicon instead of a monogram by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14635
* docs: server features are services, and handlers stay thin by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/14613
* fix(ci): pin eas-cli so mobile PR previews deploy again by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/14659
* fix(server): background GitHub polling uses ~74% fewer calls with batched GraphQL by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14673
* fix(web): show the Docker icon on dockerfile code blocks by @chrisdeeming in https://github.com/pingdotgg/t3code/pull/14675
* feat(web): update providers on every machine with one click by @t3dotgg in https://github.com/pingdotgg/t3code/pull/14678
* feat(web): beta Working section hides busy threads until they need you by @t3dotgg in https://github.com/pingdotgg/t3code/pull/13926
* fix(web): PR checks status collapses to its icon instead of wrapping by @flamboh in https://github.com/pingdotgg/t3code/pull/14700
* fix: remove outdated restart setting update advice by @t3-code[bot] in https://github.com/pingdotgg/t3code/pull/14710
* fix(web): keep the terminal toggle clear of the last header action by @Mnigos in https://github.com/pingdotgg/t3code/pull/13426
* fix(web): group composer undo the way the Lexical composer did by @chrisdeeming in https://github.com/pingdotgg/t3code/pull/14674
* fix(desktop): markdown pages no longer render invisible in the dark-mode browser by @shivamhwp in https://github.com/pingdotgg/t3code/pull/14601
* fix(mobile): one No project row at the top of the project picker by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/14532
* Remove unused isCloudDebugEnabled and isTerminalDebugEnabled by @kridaydave in https://github.com/pingdotgg/t3code/pull/14367
* fix(mobile): update Expo 58 to restore widgets and Live Activities by @juliusmarminge in https://github.com/pingdotgg/t3code/pull/14734
* fix(mobile): project picker cards match the settings card color by @juliusmarminge in https:/