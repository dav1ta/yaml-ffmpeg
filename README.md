# RENDERME is a Project for creating simple videos.

## should be defined in  yml templates



```yml
renderer:x264
default_transition:fade
combine:
  transition:nofade
  - combine:
    - src: ./video1
      from : 10s
      duraton:12s

    - src: ./video2
      from : 10s
      duraton:12s

  - effect:
      src: ./video1
      name: retro

output: ./output1
```
