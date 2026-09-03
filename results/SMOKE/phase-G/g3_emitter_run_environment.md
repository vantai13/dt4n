# G.3 emitter dry-run — host environment snapshot

Captured immediately before launch of the 64-minute run at commit `39de0adc`.
Referenced by `docs/phase-G/45-g3-emitter-dryrun-results.md`.

```text
=== captured_utc: 2026-09-03T06:24:11Z
=== git HEAD: 39de0adcb28fa39e43a2aa9f5288771cc3371420
=== platform
Linux dt4n-research-01 6.8.0-1066-gcp #74~22.04.1-Ubuntu SMP Fri Aug  7 21:51:15 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
machine x86_64
python 3.13.13
=== numpy
numpy 2.4.3
Build Dependencies:
  blas:
    detection method: pkgconfig
    found: true
    include directory: /opt/_internal/cpython-3.12.12/lib/python3.12/site-packages/scipy_openblas64/include
    lib directory: /opt/_internal/cpython-3.12.12/lib/python3.12/site-packages/scipy_openblas64/lib
    name: scipy-openblas
    openblas configuration: OpenBLAS 0.3.31.dev  USE64BITINT DYNAMIC_ARCH NO_AFFINITY
      Haswell MAX_THREADS=64
    pc file directory: /project/.openblas
    version: 0.3.31.dev
  lapack:
    detection method: pkgconfig
    found: true
    include directory: /opt/_internal/cpython-3.12.12/lib/python3.12/site-packages/scipy_openblas64/include
    lib directory: /opt/_internal/cpython-3.12.12/lib/python3.12/site-packages/scipy_openblas64/lib
    name: scipy-openblas
    openblas configuration: OpenBLAS 0.3.31.dev  USE64BITINT DYNAMIC_ARCH NO_AFFINITY
      Haswell MAX_THREADS=64
    pc file directory: /project/.openblas
    version: 0.3.31.dev
Compilers:
  c:
    commands: cc
=== cpu
allowed [0, 1, 2, 3, 4, 5, 6, 7]
CPU(s):                                  8
Model name:                              Intel(R) Xeon(R) CPU @ 2.80GHz
Thread(s) per core:                      2
NUMA node0 CPU(s):                       0-7
=== isolcpus
(none)
=== loadavg
0.72 0.22 0.14 1/1045 124497
=== top processes at launch
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
ubuntu     17470  3.1  2.4 19813592 796380 ?     Sl   02:52   6:42 /home/ubuntu/.vscode-server/cli/servers/Stable-08d4889f9ec4a1685d257b9b95de036c8e1ce1e5/server/node --dns-result-order=ipv4first /home/ubuntu/.vscode-server/cli/servers/Stable-08d4889f9ec4a1685d257b9b95de036c8e1ce1e5/server/out/bootstrap-fork --type=extensionHost --transformURIs --useHostProxy=false
1005        1890  2.4  1.6 6661364 557936 ?      Sl   02:09   6:19 java --add-opens java.base/java.nio=ALL-UNNAMED --add-opens java.base/sun.nio.ch=ALL-UNNAMED --add-opens java.base/sun.security.util=ALL-UNNAMED org.eclipse.ditto.connectivity.service.ConnectivityService
1005        1868  2.3  1.5 6379632 517368 ?      Sl   02:09   5:55 java org.eclipse.ditto.things.service.starter.ThingsService
1005        1867  2.2  1.4 6360560 479792 ?      Sl   02:09   5:40 java org.eclipse.ditto.gateway.service.starter.GatewayService
1005        1956  2.0  1.5 6370284 501500 ?      Sl   02:09   5:15 java org.eclipse.ditto.policies.service.starter.PoliciesService
1005        1950  1.6  1.4 6368676 482592 ?      Sl   02:09   4:15 java org.eclipse.ditto.thingsearch.service.starter.SearchService
ubuntu     18065  1.1  1.0 5568756 342804 ?      Sl   02:52   2:27 /home/ubuntu/.vscode-server/extensions/anthropic.claude-code-2.1.252-linux-x64/resources/native-binary/claude --output-format stream-json --verbose --input-format stream-json --max-thinking-tokens 31999 --permission-prompt-tool stdio --setting-sources=user,project,local --permission-mode auto --debug --debug-to-stderr --enable-auth-status --no-chrome --replay-user-messages
fwupd-r+    1568  0.5  0.5 668048 185772 ?       Ssl  02:09   1:24 mongod --storageEngine wiredTiger --noscripting --bind_ip_all
root         720  0.1  0.1 2489248 55608 ?       Ssl  02:09   0:23 /usr/bin/containerd
root         992  0.1  0.3 3353740 105556 ?      Ssl  02:09   0:25 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
ubuntu     17541  0.1  0.4 508172 163252 ?       Sl   02:52   0:13 /home/ubuntu/.vscode-server/extensions/openai.chatgpt-26.825.51511-linux-x64/bin/linux-x86_64/codex -c features.code_mode_host=true app-server --analytics-default-enabled
```
