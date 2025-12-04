import click
import pi0servo
import pibtinput
import pigpio

from ottopi0 import click_common_opts, get_logger


class App:
    """App class."""

    def __init__(self, btdev, pi, pins, debug=False) -> None:
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("btdev=%s, pins=%s", btdev, pins)

        self.btdev = btdev
        self.pi = pi
        self.pins = pins

        self.bt = pibtinput.PiBtInput(debug=self.__debug)
        self.prev_onkeys: dict[str, int] = {}

        self.servo = pi0servo.JsonRpcWorker(
            self.pi, self.pins, debug=self.__debug
        )
        self.parser = pi0servo.StrCmdToJson(debug=self.__debug)

    def cb_ev(self, key_name, key_state, onkeys):
        """Event Callback."""
        self.__log.debug(
            "key_name=%s,key_state=%s,onkeys=%s", key_name, key_state, onkeys
        )

        if onkeys != self.prev_onkeys:
            self.prev_onkeys = onkeys.copy()

            if key_state == pibtinput.PiBtInput.KEY["up"]:
                parsed_json = self.parser.cmdstr_to_jsonliststr("ca")
                self.servo.call(parsed_json)
                return True

            print(key_name)

            parsed_json = ""

            if key_name == "KEY_C":
                parsed_json = self.parser.cmdstr_to_jsonliststr(
                    "ms:.05 mr:5,0"
                )
                self.servo.call(parsed_json)
            if key_name == "KEY_D":
                parsed_json = self.parser.cmdstr_to_jsonliststr(
                    "ms:.05 mr:-5,0"
                )
                self.servo.call(parsed_json)

            if key_name == "KEY_E":
                parsed_json = self.parser.cmdstr_to_jsonliststr(
                    "ms:.05 mr:0,5"
                )
                self.servo.call(parsed_json)
            if key_name == "KEY_F":
                parsed_json = self.parser.cmdstr_to_jsonliststr(
                    "ms:.05 mr:0,-5"
                )
                self.servo.call(parsed_json)

            if key_name == "KEY_K":
                parsed_json = self.parser.cmdstr_to_jsonliststr(
                    "ms:.5 mv:0,0 mv:45,30 mv:0,0 mv:-45,-30 mv:0,0"
                )
                self.servo.call(parsed_json)

            if key_name == "KEY_S":
                return False

            return True

    def main(self):
        """Main."""
        self.__log.debug("")

        input_dev = self.bt.search_input_devs(self.btdev)
        self.__log.debug("input_dev=%s", input_dev)
        if not input_dev:
            self.__log.error("no such device: %s", self.btdev)
            return
        if len(input_dev) > 1:
            self.__log.error("anbiguous: %s", [d.name for d in input_dev])
            return

        print(f"input_dev: {input_dev[0]}")

        self.servo.start()

        self.bt.read_loop(input_dev[0], self.cb_ev)

    def end(self):
        """End."""
        self.__log.debug("")
        self.servo.end()


@click.command()
@click.argument("btdev", type=str, nargs=1)
@click.argument("pins", type=int, nargs=-1)
@click_common_opts("0.0.1")
def main(ctx, btdev, pins, debug):
    """Main."""
    __log = get_logger(__name__, debug)
    __log.debug("command name: %s", ctx.command.name)
    __log.debug("btdev=%s, pins=%s", btdev, pins)

    if not pins:
        __log.error("pins=%s", pins)
        return

    pi = None
    app = None
    try:
        pi = pigpio.pi()
        app = App(btdev, pi, pins, debug=debug)
        app.main()
    finally:
        click.echo("finally")
        if app:
            app.end()
        if pi:
            pi.stop()
        click.echo("done")


if __name__ == "__main__":
    main()
