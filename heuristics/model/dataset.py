import os
from typing import Dict, Optional

import pandas as pd
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms


class TorchDataset(Dataset):
    image_id_column: str = 'image_id_ext'
    label_column: str = 'result'
    img_path_column: str = 'img_path'
    sample_weight_column: str = 'sample_weight'
    img_extension: str = 'jpg'

    def __init__(
        self,
        df: pd.DataFrame,
        image_dir: str = None,
        transformer: Optional[transforms.transforms.Compose] = None,
        normalize_sample_weights: bool = True,
        with_cache=True,
    ):
        super(TorchDataset, self).__init__()
        self.image_dir = image_dir
        self.df = df.reset_index(drop=True)

        if normalize_sample_weights and (self.sample_weight_column in self.df.columns):
            self.df[self.sample_weight_column] /= self.df[self.sample_weight_column].mean()
        # self.df = self.df[self.df['result'] != -1]
        self.transformer = transformer
        self.image_cache = {}
        self.with_cache = with_cache

    def img_path_from_id(self, image_id):
        path = os.path.join(self.image_dir, f'{image_id}.{self.img_extension}')

        return path

    def get_image_path(self, item: pd.Series):
        if item.get(self.img_path_column) is None and item.get(self.image_id_column) is None:
            raise ValueError('image_id or image_path should be specified')
        image_path = item.get(self.img_path_column) or self.img_path_from_id(
            item.get(self.image_id_column)
        )

        return image_path

    def load_img(self, idx: int, item: pd.Series):
        # img = self.img_cache.get(idx)
        # if img is None:
        path = self.get_image_path(item)
        img = Image.open(path)
            # self.img_cache[idx] = img

        return img

    def __getitem__(self, idx):
        item = self.df.iloc[idx]
        label = int(item.get(self.label_column, 0))
        sample_weight = float(item.get(self.sample_weight_column, 1))

        img = self.image_cache.get(idx)
        if img is None:
            img = self.load_img(idx, item)
            if self.transformer is not None:
                img = self.transformer(img)
            if self.with_cache:
                self.image_cache[idx] = img
 
        # item = {
        #     'img': img,
        #     'label': item_series['result'],
        #     'label_name': item_series['label']
        # }

        return img, label, sample_weight

    def __len__(self):
        return len(self.df)
