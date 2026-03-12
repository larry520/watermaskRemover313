"""
命令行入口
"""
import click
from pathlib import Path
from src.watermark_remover import WatermarkRemover
from src.video_processor import VideoProcessor
from loguru import logger


@click.group()
def cli():
    """水印去除工具"""
    pass


@cli.command()
@click.option('--input', '-i', required=True, help='输入图片路径')
@click.option('--output', '-o', required=True, help='输出图片路径')
@click.option('--config', '-c', default=None, help='配置文件路径')
@click.option('--visualize', '-v', is_flag=True, help='保存检测可视化')
def remove(input, output, config, visualize):
    """去除单张图片的水印"""
    try:
        remover = WatermarkRemover(config)
        remover.remove(input, output, visualize_detection=visualize)
        click.echo(f"✓ 处理完成: {output}")
    except Exception as e:
        click.echo(f"✗ 处理失败: {e}", err=True)
        raise


@cli.command()
@click.option('--input-dir', '-i', required=True, help='输入目录')
@click.option('--output-dir', '-o', required=True, help='输出目录')
@click.option('--config', '-c', default=None, help='配置文件路径')
@click.option('--pattern', '-p', default='*.*', help='文件匹配模式')
def batch(input_dir, output_dir, config, pattern):
    """批量处理图片"""
    try:
        remover = WatermarkRemover(config)
        success_files = remover.batch_remove(input_dir, output_dir, pattern)
        click.echo(f"✓ 批量处理完成: {len(success_files)} 个文件")
    except Exception as e:
        click.echo(f"✗ 批量处理失败: {e}", err=True)
        raise


@cli.command()
@click.option('--input', '-i', required=True, help='输入视频路径')
@click.option('--output', '-o', required=True, help='输出视频路径')
@click.option('--config', '-c', default=None, help='配置文件路径')
@click.option('--start', '-s', type=float, default=None, help='开始时间（秒）')
@click.option('--end', '-e', type=float, default=None, help='结束时间（秒）')
@click.option('--skip-frames', '-k', type=int, default=1, help='跳帧处理（1=全部处理）')
@click.option('--quality', '-q', type=click.Choice(['high', 'medium', 'low']), 
              default='high', help='输出质量')
@click.option('--no-audio', is_flag=True, help='不保留音频')
@click.option('--adaptive', '-a', is_flag=True, help='使用自适应检测')
def video(input, output, config, start, end, skip_frames, quality, no_audio, adaptive):
    """处理视频去水印"""
    try:
        remover = WatermarkRemover(config)
        processor = VideoProcessor(remover, remover.config)
        
        click.echo(f"处理视频: {input}")
        
        if adaptive:
            result = processor.process_video_adaptive(
                input, output,
                quality=quality,
                keep_audio=not no_audio
            )
        else:
            result = processor.process_video(
                input, output,
                start_time=start,
                end_time=end,
                skip_frames=skip_frames,
                quality=quality,
                keep_audio=not no_audio
            )
        
        click.echo(f"\n✓ 视频处理完成!")
        click.echo(f"  输出: {result['output_path']}")
        click.echo(f"  处理帧数: {result['processed_frames']}/{result['total_frames']}")
        click.echo(f"  分辨率: {result['resolution']}")
        click.echo(f"  帧率: {result['fps']:.2f} fps")
        
    except Exception as e:
        click.echo(f"✗ 视频处理失败: {e}", err=True)
        raise


@cli.command()
@click.option('--input', '-i', required=True, help='输入视频路径')
def video_info(input):
    """查看视频信息"""
    try:
        remover = WatermarkRemover()
        processor = VideoProcessor(remover)
        
        info = processor.get_video_info(input)
        
        click.echo(f"\n视频信息:")
        click.echo(f"  路径: {info['path']}")
        click.echo(f"  分辨率: {info['resolution']}")
        click.echo(f"  帧率: {info['fps']:.2f} fps")
        click.echo(f"  总帧数: {info['total_frames']}")
        click.echo(f"  时长: {info['duration']:.2f} 秒")
        
    except Exception as e:
        click.echo(f"✗ 获取信息失败: {e}", err=True)
        raise


@cli.command()
@click.option('--input', '-i', required=True, help='输入视频路径')
@click.option('--output', '-o', required=True, help='输出视频路径')
@click.option('--config', '-c', default=None, help='配置文件路径')
@click.option('--box', '-b', type=str, default=None, 
              help='手动指定水印区域: "x1,y1,x2,y2"')
@click.option('--mask', '-m', type=str, default=None, help='使用已保存的 mask 文件')
@click.option('--quality', '-q', type=click.Choice(['high', 'medium', 'low']), 
              default='high', help='输出质量')
@click.option('--no-audio', is_flag=True, help='不保留音频')
@click.option('--save-mask', type=str, default=None, help='保存生成的 mask 到指定路径')
def fast_video(input, output, config, box, mask, quality, no_audio, save_mask):
    """快速处理视频（使用固定 Mask）⭐ 推荐"""
    try:
        from src.fast_video_processor import FastVideoProcessor
        
        remover = WatermarkRemover(config)
        processor = FastVideoProcessor(remover)
        
        click.echo(f"快速处理视频: {input}")
        
        # 解析手动区域
        manual_box = None
        if box:
            try:
                coords = [int(x.strip()) for x in box.split(',')]
                if len(coords) == 4:
                    manual_box = tuple(coords)
                    click.echo(f"使用手动区域: {manual_box}")
            except:
                click.echo("警告: 无法解析区域坐标，将自动检测", err=True)
        
        # 加载 mask
        mask_data = None
        if mask:
            import cv2
            mask_data = cv2.imread(mask, cv2.IMREAD_GRAYSCALE)
            if mask_data is None:
                click.echo(f"警告: 无法加载 mask 文件: {mask}", err=True)
            else:
                click.echo(f"使用加载的 Mask: {mask}")
        
        # 处理
        result = processor.process_video_with_fixed_mask(
            input, output,
            mask=mask_data,
            manual_box=manual_box,
            detect_from_first_frame=(mask_data is None and manual_box is None),
            quality=quality,
            keep_audio=not no_audio
        )
        
        # 保存 mask
        if save_mask and processor.fixed_mask is not None:
            processor.save_mask(save_mask)
            click.echo(f"✓ Mask 已保存: {save_mask}")
        
        click.echo(f"\n✓ 视频处理完成!")
        click.echo(f"  输出: {result['output_path']}")
        click.echo(f"  总帧数: {result['total_frames']}")
        click.echo(f"  分辨率: {result['resolution']}")
        click.echo(f"  Mask: {result['mask_path']}")
        
    except Exception as e:
        click.echo(f"✗ 快速处理失败: {e}", err=True)
        raise


@cli.command()
@click.option('--input', '-i', required=True, help='输入图片路径')
@click.option('--config', '-c', default=None, help='配置文件路径')
def detect(input, config):
    """仅检测水印（不修复）"""
    try:
        remover = WatermarkRemover(config)
        detections = remover.detect_only(input)
        
        if not detections:
            click.echo("未检测到文字")
            return
        
        click.echo(f"\n检测到 {len(detections)} 个文字区域:\n")
        for i, det in enumerate(detections, 1):
            mark = "✓" if det['is_watermark'] else "✗"
            click.echo(f"{i}. {mark} '{det['text']}' (置信度: {det['confidence']:.2f})")
            click.echo(f"   位置: {det['box']}")
            click.echo(f"   是否为水印: {'是' if det['is_watermark'] else '否'}\n")
            
    except Exception as e:
        click.echo(f"✗ 检测失败: {e}", err=True)
        raise


@cli.command()
@click.option('--config', '-c', default=None, help='配置文件路径')
def info(config):
    """显示系统信息"""
    try:
        remover = WatermarkRemover(config)
        system_info = remover.get_system_info()
        
        click.echo("\n=== 系统信息 ===\n")
        
        click.echo("OCR 检测器:")
        click.echo(f"  语言: {', '.join(system_info['detector']['languages'])}")
        click.echo(f"  GPU: {'是' if system_info['detector']['gpu'] else '否'}")
        
        click.echo("\n图像修复:")
        inpainter_info = system_info['inpainter']
        click.echo(f"  使用 IOPaint: {'是' if inpainter_info['using_iopaint'] else '否'}")
        click.echo(f"  模型: {inpainter_info['model_name']}")
        click.echo(f"  设备: {inpainter_info['device']}")
        
        click.echo()
        
    except Exception as e:
        click.echo(f"✗ 获取信息失败: {e}", err=True)
        raise


if __name__ == '__main__':
    cli()
