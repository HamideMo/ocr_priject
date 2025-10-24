import pandas as pd
from PIL import Image
import os
import glob
from datasets import Dataset, DatasetDict
import json

def create_trocr_dataset(data_path, output_dataset_path):
    """
    ایجاد دیتاست مناسب برای مدل TrOCR
    """
    print("🚀 شروع ایجاد دیتاست TrOCR...")
    
    # خواندن تمام متن‌ها
    text_files = sorted(glob.glob(os.path.join(data_path, 'fulltext', '*.txt')))
    image_files = sorted(glob.glob(os.path.join(data_path, 'images', '*.png')))
    
    print(f"📖 تعداد فایل‌های متن: {len(text_files)}")
    print(f"🖼️  تعداد فایل‌های تصویر: {len(image_files)}")
    
    # ایجاد لیست نمونه‌ها
    samples = []
    
    for i, (text_file, image_file) in enumerate(zip(text_files, image_files)):
        try:
            # خواندن متن
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            
            # بررسی اینکه تصویر وجود دارد
            if not os.path.exists(image_file):
                print(f"⚠️  تصویر {image_file} وجود ندارد")
                continue
            
            # اضافه کردن به نمونه‌ها
            samples.append({
                'image_path': image_file,
                'text': text
            })
            
            if (i + 1) % 100 == 0:
                print(f"📦 {i + 1} نمونه پردازش شد...")
                
        except Exception as e:
            print(f"❌ خطا در پردازش نمونه {i}: {e}")
    
    print(f"✅ {len(samples)} نمونه آماده شد")
    
    # تقسیم داده‌ها به train/validation/test
    train_size = int(0.8 * len(samples))
    val_size = int(0.1 * len(samples))
    
    train_samples = samples[:train_size]
    val_samples = samples[train_size:train_size + val_size]
    test_samples = samples[train_size + val_size:]
    
    print(f"\n📊 تقسیم داده‌ها:")
    print(f"   🏋️  آموزش: {len(train_samples)} نمونه")
    print(f"   📊 اعتبارسنجی: {len(val_samples)} نمونه")
    print(f"   🧪 تست: {len(test_samples)} نمونه")
    
    # ایجاد دیتاست Hugging Face
    def create_hf_dataset(samples_list):
        """تبدیل لیست نمونه‌ها به دیتاست Hugging Face"""
        dataset = Dataset.from_dict({
            'image': [sample['image_path'] for sample in samples_list],
            'text': [sample['text'] for sample in samples_list]
        })
        return dataset
    
    # ایجاد دیتاست‌های مختلف
    train_dataset = create_hf_dataset(train_samples)
    val_dataset = create_hf_dataset(val_samples)
    test_dataset = create_hf_dataset(test_samples)
    
    # ایجاد DatasetDict
    dataset_dict = DatasetDict({
        'train': train_dataset,
        'validation': val_dataset,
        'test': test_dataset
    })
    
    # ذخیره دیتاست
    dataset_dict.save_to_disk(output_dataset_path)
    print(f"💾 دیتاست در '{output_dataset_path}' ذخیره شد")
    
    return dataset_dict

def test_dataset_loading(dataset_path):
    """
    تست بارگذاری دیتاست
    """
    print("\n🔍 تست بارگذاری دیتاست...")
    
    from datasets import load_from_disk
    
    try:
        dataset = load_from_disk(dataset_path)
        
        print("✅ دیتاست با موفقیت بارگذاری شد")
        print(f"📁 ساختار: {dataset}")
        
        # نمایش یک نمونه
        print(f"\n👀 نمونه از داده آموزش:")
        sample = dataset['train'][0]
        print(f"   📄 متن: {sample['text'][:100]}...")
        print(f"   🖼️  مسیر تصویر: {sample['image']}")
        
        # تست نمایش تصویر
        try:
            img = Image.open(sample['image'])
            print(f"   📐 ابعاد تصویر: {img.size}")
        except Exception as e:
            print(f"   ⚠️  خطا در نمایش تصویر: {e}")
            
        return dataset
        
    except Exception as e:
        print(f"❌ خطا در بارگذاری دیتاست: {e}")
        return None

# مسیرها
data_path = "/home/f_allahmoradi/Desktop/TROCR/selected_1000_data"
output_dataset_path = "/home/f_allahmoradi/Desktop/TROCR/trocr_dataset"

# ایجاد دیتاست
print("🔄 در حال ایجاد دیتاست...")
dataset = create_trocr_dataset(data_path, output_dataset_path)

# تست دیتاست
if dataset:
    test_dataset_loading(output_dataset_path)
