import os
import argparse
import shutil
from utils.hashes import get_hash
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm

PHOTO_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff', '.svg', '.heic']
VIDEO_FORMATS = ['.mp4', '.gif', '.mov', '.webm', '.avi', '.wmv', '.rm', '.mpg', '.mpe', '.mpeg', '.mkv', '.m4v', '.mts', '.m2ts']


def run(source, move_to, dry_run):
    for root, _, files in os.walk(source):
        if files:
            relpath = os.path.relpath(root, source)
            print(f'Scanning {relpath}')
            
            # 1. get file hashes
            print(f'>> Hashing {len(files)} files...')
            images_by_hash = defaultdict(list)
            images_by_name = defaultdict(list)
            for file in tqdm(files, leave=False):
                fname, fext = os.path.splitext(file)
                if fext.lower() not in PHOTO_FORMATS:
                    # ignore non-image files
                    continue

                fpath = os.path.join(root, file)
                images_by_hash[get_hash(fpath)].append(file)
                images_by_name[fname].append(file)

            # 2. find if any file is live photo (by file name)
            print('>> Looking for live photos...')
            lives_by_name = defaultdict(list)
            for file in files:
                fname, fext = os.path.splitext(file)
                if fext.lower() not in VIDEO_FORMATS:
                    # ignore non-video files
                    continue

                if fname in images_by_name:
                    lives_by_name[fname].append(file)

            # 3. rank the files: file with live photo on top, then sort alphabetically
            print('>> Ranking files...')
            dupes = []
            for _, images in tqdm(images_by_hash.items(), total=len(images_by_hash), leave=False):
                if len(images) > 1:
                    images_with_live = []
                    images_without_live = []
                    for file in images:
                        fname, _ = os.path.splitext(file)
                        if fname in lives_by_name:
                            images_with_live.append((file, lives_by_name[fname]))
                        else:
                            images_without_live.append((file, []))

                    dupes.append(sorted(images_with_live, key=lambda x: os.path.splitext(x[0])[0]) + 
                                 sorted(images_without_live, key=lambda x: os.path.splitext(x[0])[0]))

            # 4. keep the first one, remove the others (including their live photo MOV)
            if not dupes:
                print('>> No dupe found')
            else:
                print(f'>> Found {len(dupes)} dupes')

                # make dir
                newdir = os.path.join(move_to, relpath)
                print(f'.... Making directory {newdir}')
                if not dry_run:
                    os.makedirs(newdir, exist_ok=True)

                for images in dupes:
                    # print(f'.... Dupe Group: {",".join([i for i, _ in images])}')
                    # keep first one
                    if images[0][1]:
                        # live
                        print(f'.... + Keeping {images[0][0]} with {images[0][1]}')
                    else:
                        print(f'.... + Keeping {images[0][0]}')

                    # move images
                    for image, videos in images[1:]:
                        if videos:
                            print(f'.... - Moving {image} with {videos}')
                        else:
                            print(f'.... - Moving {image}')

                        if not dry_run:
                            try:
                                shutil.move(os.path.join(root, image), newdir)
                            except FileNotFoundError:
                                # ignore if file is already removed
                                pass

                        for video in videos:
                            if not dry_run:
                                try:
                                    shutil.move(os.path.join(root, video), newdir)
                                except FileNotFoundError:
                                    pass


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('move_to')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = get_args()
    run(args.source, args.move_to, args.dry_run)