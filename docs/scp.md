```
    from current location:
    scp jetson@192.168.144.114:/mnt/nvme/1.txt .
   
```

```
docker logs --tail 10000 docker_name > /mnt/nvme/last_10000.txt 2>&1

2>&1
1 - stdout
2 - stderr
redirects stderr (2) to the same destination as stdout.

```

```
ssh username@192.168.144.114 \
"tail -n 150 -f /mnt/nvme/outputs/air_Master_26_11_2026_15_48_40.txt"
```