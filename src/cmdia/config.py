import sys
import pathlib
import pydantic
import yaml
from typing import List


class Config(pydantic.BaseModel):
    media_player: List[str] = ['mpv']
    watched_marker: str = '[✔]'


def load_config() -> Config:
    config_file = pathlib.Path(pathlib.Path.home(), '.config', '', 'config.yaml')
    config_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_file, 'r') as f:
            config_yaml = yaml.safe_load(f)
    except FileNotFoundError:
        config = Config()
        with open(config_file, 'w') as f:
            f.write(yaml.dump(config.model_dump()))
        return config

    try:
        return Config.model_validate(config_yaml)
    except pydantic.ValidationError as e:
        print('Unable to parse config file', file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(1)
