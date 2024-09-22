import asyncio
import logging
import sys
from asyncio import sleep
from datetime import datetime
from random import randint

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import F
from aiogram.types import FSInputFile
from PIL import Image

API_TOKEN = '7680499594:AAGCej4YBUexbLu9uWbmJtbBvFaPi-A8tQw'

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)


# State management for photo collection
class PhotoCollector(StatesGroup):
    waiting_for_photos = State()


# State management for document processing
class ZipProcessor(StatesGroup):
    waiting_for_zip = State()


welcome_text = """Welcome to the 3D mapping data processing bot
You can steal data!

Note: Upload data in the form of archive: Zip, Rar"""
# Memory for images
user_images = {}


# Start command handler
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(welcome_text)
    await state.set_state(ZipProcessor.waiting_for_zip)


# Photo handler (collects up to 36)
@dp.message(PhotoCollector.waiting_for_photos, F.photo)
async def handle_photos(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    photos = user_images.get(user_id, [])

    if len(photos) >= 36:
        await message.answer("You've already sent 36 photos. Please wait while I process them.")
        return

    # Download photo
    photo = message.photo[-1]  # get the highest resolution photo
    photo_file = await bot.download(photo.file_id)

    # Store it in memory
    photos.append(photo_file)
    user_images[user_id] = photos

    await sleep(1000)
    await message.answer(f"Received {len(photos)}/36 photos.")

    # Once 36 photos are collected, assemble the final image
    if len(photos) == 36:
        await message.answer("Processing the final image. Please wait...")
        final_image_path = await process_photos(user_id, photos)
        if final_image_path:
            # Send final image to the user
            await bot.send_photo(user_id, photo=FSInputFile(final_image_path), caption="Here's your assembled image!")
        else:
            await message.answer("Something went wrong during image processing.")
        user_images[user_id] = []  # Clear the user images after processing
        await state.clear()


# Document (ZIP) handler
@dp.message(F.document.mime_type == 'application/zip')
async def handle_zip(message: types.Message):
    await message.answer("ZIP file received! Starting processing...")
    await asyncio.sleep(1)

    # Send 10 different fake messages every second
    fake_messages = [
        "Extracting files...",
        "Analyzing images...",
        "Cleaning up data...",
        "Optimizing photo quality...",
        "Resizing images...",
        "Combining images...",
        "Removing duplicates...",
        "Enhancing colors...",
        "Compressing the output...",
        "Finalizing the image...",
    ]

    for msg in fake_messages:
        await message.answer(msg)
        await asyncio.sleep(randint(1, 6))  # Wait for 1 second between each message

    # After processing, send a final image (a stored image on the local system)
    final_image_path = "final_image.jpg"  # Path to the stored final image
    await message.answer("Processing complete! Sending the final image.")

    now = datetime.now()
    file_name = f'final_image{now.strftime("%m/%d/%Y, %H:%M:%S")}.jpg'
    # Correct way to send the final image using InputFile
    await bot.send_photo(message.chat.id, photo=FSInputFile(final_image_path, file_name))


# Function to process and assemble the photos with trimming of overlapping parts
async def process_photos(user_id, photos):
    # Define the trimming of overlapping parts (in pixels)
    overlap_x = 50  # Trim 50px from left and right
    overlap_y = 50  # Trim 50px from top and bottom

    # Image size before trimming (assumed original size)
    original_img_size = (1080, 1080)

    # Calculate the size after trimming the overlap
    trimmed_img_size = (original_img_size[0] - 2 * overlap_x, original_img_size[1] - 2 * overlap_y)

    # Create a blank canvas for the final image
    grid_size = (6, 6)  # 6x6 grid
    final_image = Image.new('RGB', (trimmed_img_size[0] * grid_size[0], trimmed_img_size[1] * grid_size[1]),
                            (255, 255, 255))

    # Open and paste each image in the grid (starting from bottom-left, going upwards in columns)
    for idx, photo in enumerate(photos):
        with Image.open(photo) as img:
            img = img.resize(original_img_size)  # Resize each image to the original assumed size
            # Crop the image to remove the overlapping parts
            img = img.crop((overlap_x, overlap_y, original_img_size[0] - overlap_x, original_img_size[1] - overlap_y))

            # Determine the row and column based on the index (bottom-up, left-right)
            col = idx % grid_size[0]  # Calculate the column
            row = idx // grid_size[1]  # Calculate the row (from bottom)

            # Calculate where to paste the image on the final canvas
            x = col * trimmed_img_size[0]
            y = (grid_size[1] - row - 1) * trimmed_img_size[1]  # Bottom-up placement for each column

            # Paste the cropped image in its place
            final_image.paste(img, (x, y))

    # Save the final image
    output_path = f"{user_id}_final_image.jpg"
    final_image.save(output_path)

    return output_path


# Error handler if the user sends non-photo
@dp.message(PhotoCollector.waiting_for_photos)
async def not_a_photo(message: types.Message):
    await message.answer("Please send a JPG image.")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
