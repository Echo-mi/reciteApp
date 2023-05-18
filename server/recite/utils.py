# -*- coding:utf-8 -*-
import logging
import re
import base64
from uuid import uuid4
from io import BytesIO
from typing import Any

import msgpack
from pydub import AudioSegment

from .settings import APP_ID, API_KEY, SECRETE_KEY
from .aip.aio_speech import AipSpeech

_Logger = logging.getLogger()
AipClient = AipSpeech(APP_ID, API_KEY, SECRETE_KEY)
CHINESE_RE_PAT = re.compile(r"[\u4e00-\u9fa5]")


def pack(obj: Any):

    return msgpack.packb(obj, use_bin_type=True)


def unpack(obj: Any):

    return msgpack.unpackb(obj, raw=False)


async def aip_tts(text: str):
    voice_option = {
        "vol": 5,
        "per": 4,
        "spd": 4,
    }
    synthesis_audio = await AipClient.synthesis(text, options=voice_option)
    return synthesis_audio


def test_json(filepath, read_ahead_limit=-1):
    """Return json dictionary with media info(codec, duration, size, bitrate...) from filepath
    """
    from pydub.utils import get_prober_name, fsdecode, PIPE, _fd_or_path_or_tempfile, Popen
    import json
    prober = get_prober_name()
    command_args = [
        "-v", "info",
        "-show_format",
        "-show_streams",
    ]
    try:
        command_args += [fsdecode(filepath)]
        stdin_parameter = None
        stdin_data = None
    except TypeError:
        if prober == 'ffprobe':
            command_args += ["-read_ahead_limit", str(read_ahead_limit),
                             "cache:pipe:0"]
        else:
            command_args += ["-"]
        stdin_parameter = PIPE
        file, close_file = _fd_or_path_or_tempfile(filepath, 'rb', tempfile=False)
        file.seek(0)
        stdin_data = file.read()
        if close_file:
            file.close()

    command = [prober, '-of', 'json'] + command_args
    _Logger.error(command)
    res = Popen(command, stdin=stdin_parameter, stdout=PIPE, stderr=PIPE)
    output, stderr = res.communicate(input=stdin_data)
    output = output.decode("utf-8", 'ignore')
    stderr = stderr.decode("utf-8", 'ignore')

    _Logger.error(output)
    _Logger.error(stderr)
    info = json.loads(output)


class TestAudioSegment(AudioSegment):
    @classmethod
    def from_file(cls, file, format=None, codec=None, parameters=None, start_second=None, duration=None, **kwargs):
        from pydub.audio_segment import fsdecode, _fd_or_path_or_tempfile, AUDIO_FILE_EXT_ALIASES, mediainfo_json, CouldntDecodeError, fix_wav_headers, log_conversion
        import subprocess
        orig_file = file
        try:
            filename = fsdecode(file)
        except TypeError:
            filename = None
        file, close_file = _fd_or_path_or_tempfile(file, 'rb', tempfile=False)

        if format:
            format = format.lower()
            format = AUDIO_FILE_EXT_ALIASES.get(format, format)

        def is_format(f):
            f = f.lower()
            if format == f:
                return True

            if filename:
                return filename.lower().endswith(".{0}".format(f))

            return False

        if is_format("wav"):
            try:
                if start_second is None and duration is None:
                    return cls._from_safe_wav(file)
                elif start_second is not None and duration is None:
                    return cls._from_safe_wav(file)[start_second * 1000:]
                elif start_second is None and duration is not None:
                    return cls._from_safe_wav(file)[:duration * 1000]
                else:
                    return cls._from_safe_wav(file)[start_second * 1000:(start_second + duration) * 1000]
            except:
                file.seek(0)
        elif is_format("raw") or is_format("pcm"):
            sample_width = kwargs['sample_width']
            frame_rate = kwargs['frame_rate']
            channels = kwargs['channels']
            metadata = {
                'sample_width': sample_width,
                'frame_rate': frame_rate,
                'channels': channels,
                'frame_width': channels * sample_width
            }
            if start_second is None and duration is None:
                return cls(data=file.read(), metadata=metadata)
            elif start_second is not None and duration is None:
                return cls(data=file.read(), metadata=metadata)[start_second * 1000:]
            elif start_second is None and duration is not None:
                return cls(data=file.read(), metadata=metadata)[:duration * 1000]
            else:
                return cls(data=file.read(), metadata=metadata)[start_second * 1000:(start_second + duration) * 1000]

        conversion_command = [cls.converter,
                              '-y',  # always overwrite existing files
                              ]

        # If format is not defined
        # ffmpeg/avconv will detect it automatically
        if format:
            conversion_command += ["-f", format]

        if codec:
            # force audio decoder
            conversion_command += ["-acodec", codec]

        read_ahead_limit = kwargs.get('read_ahead_limit', -1)
        if filename:
            conversion_command += ["-i", filename]
            stdin_parameter = None
            stdin_data = None
        else:
            if cls.converter == 'ffmpeg':
                conversion_command += ["-read_ahead_limit", str(read_ahead_limit),
                                       "-i", "cache:pipe:0"]
            else:
                conversion_command += ["-i", "-"]
            stdin_parameter = subprocess.PIPE
            stdin_data = file.read()

        if codec:
            info = None
        else:
            info = mediainfo_json(orig_file, read_ahead_limit=read_ahead_limit)
        if info:
            audio_streams = [x for x in info['streams']
                             if x['codec_type'] == 'audio']
            # This is a workaround for some ffprobe versions that always say
            # that mp3/mp4/aac/webm/ogg files contain fltp samples
            audio_codec = audio_streams[0].get('codec_name')
            if (audio_streams[0].get('sample_fmt') == 'fltp' and
                    audio_codec in ['mp3', 'mp4', 'aac', 'webm', 'ogg']):
                bits_per_sample = 16
            else:
                bits_per_sample = audio_streams[0]['bits_per_sample']
            if bits_per_sample == 8:
                acodec = 'pcm_u8'
            else:
                acodec = 'pcm_s%dle' % bits_per_sample

            conversion_command += ["-acodec", acodec]

        conversion_command += [
            "-vn",  # Drop any video streams if there are any
            "-f", "wav"  # output options (filename last)
        ]

        if start_second is not None:
            conversion_command += ["-ss", str(start_second)]

        if duration is not None:
            conversion_command += ["-t", str(duration)]

        conversion_command += ["-"]

        if parameters is not None:
            # extend arguments with arbitrary set
            conversion_command.extend(parameters)

        log_conversion(conversion_command)

        p = subprocess.Popen(conversion_command, stdin=stdin_parameter,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p_out, p_err = p.communicate(input=stdin_data)
        # _Logger.error(p_out.decode(errors='ignore'))
        # _Logger.error(conversion_command)
        if p.returncode != 0 or len(p_out) == 0:
            if close_file:
                file.close()
            raise CouldntDecodeError(
                "Decoding failed. ffmpeg returned error code: {0}\n\nOutput from ffmpeg/avlib:\n\n{1}".format(
                    p.returncode, p_err.decode(errors='ignore')))

        p_out = bytearray(p_out)
        fix_wav_headers(p_out)
        p_out = bytes(p_out)
        obj = cls(p_out)

        if close_file:
            file.close()

        if start_second is None and duration is None:
            return obj
        elif start_second is not None and duration is None:
            return obj[0:]
        elif start_second is None and duration is not None:
            return obj[:duration * 1000]
        else:
            return obj[0:duration * 1000]


async def aip_asr(audio_bytes):
    audio_bytes_io = BytesIO(audio_bytes.body)
    audio_bytes = TestAudioSegment.from_file(audio_bytes_io)._data
    res = await AipClient.asr(audio_bytes) or {}
    return res


def split_sentence(sentence, pivot):
    '''把识别的整句分开
    '''
    # 用 逗号 分离句子
    sentences = sentence.split("，")
    for s in sentences:
        if pivot in s:
            # 仅留下中文
            s = "".join(list(re.findall(CHINESE_RE_PAT, s)))
            return s

    return ""