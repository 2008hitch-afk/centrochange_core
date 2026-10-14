"""Fail-closed command routing for a full isolated #139 executor rehearsal."""
from pathlib import Path

PROJECT = 'cc139-w5-isolated'
IMAGE_PREFIX = 'centrochange-single:issue139-e2e-'


class IsolationError(ValueError):
    pass


def _inside(path, root):
    return Path(path).resolve().is_relative_to(root.resolve())


def scope_command(args, *, root, image):
    """Route only known executor Docker commands to the clone.

    No shell expansion is used. Compose files, env, copy paths and names must
    remain inside the private rehearsal or have the exact clone prefix.
    """
    if not isinstance(args, (list, tuple)) or not args or image.startswith(IMAGE_PREFIX) is False:
        raise IsolationError('invalid rehearsal command or image')
    args = [str(x) for x in args]
    if args[0] != 'docker':
        if args[0] not in ('git', 'gpg', 'runuser'):
            raise IsolationError('non-Docker operation outside isolated executor scope')
        if any('centrochange-dev' in x for x in args):
            raise IsolationError('non-Docker command references DEV')
        return args
    scoped = [x.replace('centrochange-dev-', PROJECT + '-') for x in args]
    if any('centrochange-dev' in x for x in scoped):
        raise IsolationError('Docker command references DEV after routing')
    if len(scoped) < 2:
        raise IsolationError('Docker operation missing')
    verb = scoped[1]
    if verb == 'compose':
        if '-p' not in scoped or scoped[scoped.index('-p') + 1] != PROJECT:
            raise IsolationError('Compose project differs from clone')
        if '--env-file' not in scoped or not _inside(scoped[scoped.index('--env-file') + 1], root):
            raise IsolationError('Compose env is not private')
        positions = [i for i, value in enumerate(scoped) if value == '-f']
        if not positions or any(i + 1 >= len(scoped) or not _inside(scoped[i + 1], root)
                                for i in positions):
            raise IsolationError('Compose file is not private')
        if not any(value in ('config', 'stop', 'up', 'ps', 'down') for value in scoped):
            raise IsolationError('Compose operation not allowed')
    elif verb == 'exec':
        names = [x for x in scoped[2:] if x.startswith(PROJECT + '-') and x.endswith('-1')]
        if len(names) != 1:
            raise IsolationError('Docker exec lacks one clone target')
    elif verb == 'cp':
        if len(scoped) != 4:
            raise IsolationError('Docker cp syntax differs')
        clone_paths = [x for x in scoped[2:] if x.startswith(PROJECT + '-backend-1:')]
        local_paths = [x for x in scoped[2:] if ':' not in x]
        if len(clone_paths) != 1 or len(local_paths) != 1 or not _inside(local_paths[0], root):
            raise IsolationError('Docker cp crosses clone boundary')
    elif verb == 'inspect':
        targets = [x for x in scoped[2:] if x.startswith(PROJECT + '-') and x.endswith('-1')]
        if len(targets) != 1:
            raise IsolationError('Docker inspect target differs')
    elif verb == 'image':
        if len(scoped) < 4 or scoped[2] != 'inspect':
            raise IsolationError('Docker image operation not read-only inspect')
    elif verb == 'build':
        if '-t' not in scoped or scoped[scoped.index('-t') + 1] != image or \
                not _inside(scoped[-1], root) or '--network=none' not in scoped:
            raise IsolationError('Docker build target or context differs')
    elif verb == 'run':
        if '--network=none' not in scoped or any(x in ('-v', '--volume', '--mount') for x in scoped):
            raise IsolationError('Docker run could mount shared resources')
        if image not in scoped and 'centrochange-single:goal02-abc-fixture-83f8f4f' not in scoped:
            raise IsolationError('Docker run image differs')
    elif verb == 'tag':
        if len(scoped) != 4 or scoped[2] != \
                'sha256:f200dc3b0206a8ecc1ce2eae72c27d96e0d1a145fd88cbb3efaa33a49cdcc3af' or \
                not scoped[3].startswith('centrochange-single:issue139-rollback-'):
            raise IsolationError('Docker rollback tag differs')
    else:
        raise IsolationError('Docker operation outside isolated executor scope')
    return scoped
