# Recording Your Screen and Audio with FFmpeg:
```
ffmpeg -f x11grab -video_size 1920x1080 -framerate 30 -i :1.0+0,0 -f pulse -i alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__hw_sofhdadsp_6__source -f pulse -i alsa_output.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__hw_sofhdadsp__sink.monitor -map 0:v -map 1:a -map 2:a -c:v libx264 -preset veryfast -crf 23 -c:a aac -b:a 192k output.mp4
```