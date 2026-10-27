# ComfyUI API workflows

Export workflows in **API format** from ComfyUI and save them here using these filenames:

- `image_to_video.json`
- `text_to_image.json`
- `chat_to_image.json`
- `text_to_video.json`
- `controlled_video.json`
- `video_finetune.json`
- `clip_ideation.json`
- `ugc_avatar.json`
- `lip_sync.json`
- `product_placement.json`
- `motion_transfer.json`
- `generative_broll.json`

The adapter replaces `{{prompt}}`, `{{image}}`, and `{{video}}` anywhere in the workflow JSON before queueing it. This keeps model and node choices under the local user's control instead of hard-coding incompatible checkpoints.
