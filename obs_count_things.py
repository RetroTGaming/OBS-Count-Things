import obspython as obs
from os.path import exists


class TextContent:
    def __init__(self, source_name=None, text_string="This is default text"):
        self.source_name = source_name
        self.text_string = text_string
        self.counter = 0
        
        obs.script_log(obs.LOG_INFO, f"Initializing TextContent with counter of {self.counter}")

    def set_counter(self, count):
        print(f"Setting counter to {count}")
        self.counter = count

    def update_text(self, counter_text, counter_value=0):
        source = obs.obs_get_source_by_name(self.source_name)
        settings = obs.obs_data_create()

        if counter_value == 1:
            self.counter += 1

        elif counter_value == -1:
            self.counter -= 1

        elif counter_value == 0:
            self.counter = 0

        self.text_string = f"{counter_text}{self.counter:,}"

        try:
            print(f"Writing new saved counter to settings file of {self.counter}")
            with open(self.counter_save_path, 'w+') as f:
                f.write(str(self.counter))
        except:
            print("ERROR: Something went wrong trying to save new counter value")

        obs.obs_data_set_string(settings, "text", self.text_string)
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)


class Driver(TextContent):
    def increment(self):
        self.update_text(self.counter_text, 1)

    def decrement(self):
        self.update_text(self.counter_text, -1)

    def reset(self):
        self.update_text(self.counter_text, 0)


class Hotkey:
    def __init__(self, callback, obs_settings, _id):
        self.obs_data = obs_settings
        self.hotkey_id = obs.OBS_INVALID_HOTKEY_ID
        self.hotkey_saved_key = None
        self.callback = callback
        self._id = _id

        self.load_hotkey()
        self.register_hotkey()
        self.save_hotkey()

    def register_hotkey(self):
        description = "OBS Count Things " + str(self._id)
        self.hotkey_id = obs.obs_hotkey_register_frontend(
            "htk_id" + str(self._id), description, self.callback
        )
        obs.obs_hotkey_load(self.hotkey_id, self.hotkey_saved_key)

    def load_hotkey(self):
        self.hotkey_saved_key = obs.obs_data_get_array(
            self.obs_data, "htk_id" + str(self._id)
        )
        obs.obs_data_array_release(self.hotkey_saved_key)

    def save_hotkey(self):
        self.hotkey_saved_key = obs.obs_hotkey_save(self.hotkey_id)
        obs.obs_data_set_array(
            self.obs_data, "htk_id" + str(self._id), self.hotkey_saved_key
        )
        obs.obs_data_array_release(self.hotkey_saved_key)


class HotkeyDataHolder:
    htk_copy = None  # this attribute will hold instance of Hotkey


hotkeys_counter = Driver()
h01 = HotkeyDataHolder()
h02 = HotkeyDataHolder()
h03 = HotkeyDataHolder()


def callback_up(pressed):
    if pressed:
        return hotkeys_counter.increment()


def callback_down(pressed):
    if pressed:
        return hotkeys_counter.decrement()


def callback_reset(pressed):
    if pressed:
        return hotkeys_counter.reset()


def script_description():
    return "We count things via OBS hotkey. See github.com/RetroTGaming/OBS-Count-Things for instructions"


def script_update(settings):
    hotkeys_counter.source_name = obs.obs_data_get_string(settings, "source")
    hotkeys_counter.counter_text = obs.obs_data_get_string(settings, "counter_text")
    hotkeys_counter.counter_save_path = f"{obs.obs_data_get_string(settings, 'counter_save_path')}\\obs_count_things_counter.txt"

    if hotkeys_counter.counter_save_path is None or str(hotkeys_counter.counter_save_path).strip() == "":
        print("Got no save path, will initialize using 0")

    else:
        print(f"Got save path of {hotkeys_counter.counter_save_path}")

        try:
            if exists(hotkeys_counter.counter_save_path):
                with open(hotkeys_counter.counter_save_path, "r") as f:
                    first = f.read().split('\n')[0]
                    print(f"Read settings file, got {first} - will set counter to start at this number.")
                    hotkeys_counter.set_counter(int(first))

            else:
                with open(hotkeys_counter.counter_save_path, 'w+') as f:
                    f.write('0')
        except:
            print("! ERROR: This happened while dealing with the settings file. Will start at 0 and carry on.")


def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_text(
        props, "counter_text", "Set Counter Text", obs.OBS_TEXT_DEFAULT
    )

    obs.obs_properties_add_text(
        props, "counter_save_path", "Set Counter Save Path", obs.OBS_TEXT_DEFAULT
    )

    p1 = obs.obs_properties_add_list(
        props,
        "source",
        "Text Source",
        obs.OBS_COMBO_TYPE_EDITABLE,
        obs.OBS_COMBO_FORMAT_STRING,
    )

    sources = obs.obs_enum_sources()

    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if source_id == "text_gdiplus" or source_id == "text_ft2_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p1, name, name)

        obs.source_list_release(sources)

    return props


def script_load(settings):
    h01.htk_copy = Hotkey(callback_up, settings, "count_up")
    h02.htk_copy = Hotkey(callback_down, settings, "count_down")
    h03.htk_copy = Hotkey(callback_reset, settings, "reset")

def script_save(settings):
    for h in [h01, h02, h03]:
        h.htk_copy.save_hotkey()
