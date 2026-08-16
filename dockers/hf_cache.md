# Check hf cache:
```
echo $HF_HUB_CACHE
echo $HF_HOME
echo $XDG_CACHE_HOME
```

# change HF cache:
```
export HF_HOME=/mnt/nvme/huggingface
source ~/.bashrc
python -c "from huggingface_hub import constants; print(constants.HF_HOME); print(constants.HF_HUB_CACHE)"
```