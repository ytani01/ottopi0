#
# (c) 2025 Yoichi Tanibayashi
#
import click


def click_common_opts(
    ver_str: str = "",
    use_h: bool = True,
    use_d: bool = True,
    use_v: bool = False,
):
    """共通オプションをまとめたメタデコレータ"""

    def _decorator(func):
        decorators = []

        if len(ver_str) > 0:
            v_str = ver_str
        else:
            v_str = "_._._"

        # version option
        ver_opts = ["--version", "-V"]
        if use_v:
            ver_opts.append("-v")
        decorators.append(
            click.version_option(
                v_str, *ver_opts, message="%(prog)s %(version)s"
            )
        )

        # debug option
        debug_opts = ["--debug"]
        if use_d:
            debug_opts.append("-d")
        decorators.append(
            click.option(*debug_opts, is_flag=True, help="debug flag")
        )

        # help option
        help_opts = ["--help"]
        if use_h:
            help_opts.append("-h")
        decorators.append(click.help_option(*help_opts))

        # decorators をまとめて適用
        for dec in reversed(decorators):
            func = dec(func)

        # context を最後に wrap
        return click.pass_context(func)

    return _decorator
