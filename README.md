# THIS IS A WORK IN PROGRESS USE AT YOUR OWN RISK!!!!!!!

# REPORT BUGS AND SUGGEST IMPROVEMENTS!!!!

#### Some of the concluded features can change durring Beta

# BETA ROADMAP

- [x] Config Flow \*
- [x] Categories
- [x] Accounts
- [x] Bills in calendar
- [x] Import Piggy Banks
- [ ] Import Budgets
- [ ] Services
- [ ] Add to HACS

# Planned Improvements

- [ ] Translations
- [ ] Auto create Webhooks in FireflyIII
- [ ] Handle Webhooks to instant response
- [ ] Tests

\* - Please note that I’ll not be retrofitting configs to versions until its final! So on some releases of beta I’ll add to the release notes a information to delete the integration and add it again. No need to remove from HACS, just remove from Home Assistant and make the config again!

Feedbacks are more than welcome, also feature requests.

#

#

# FireflyIII Integration

_Component to integrate with [FireflyIII][fireflyiii]._

[fireflyiii]: https://www.firefly-iii.org/

**This component will set up the following platforms.**

| Platform   | Description                       |
| ---------- | --------------------------------- |
| `sensor`   | Show info from an FireflyIII API. |
| `calendar` | Calendar for bills                |

## Installation via HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=firstof9&repository=fireflyiii)

1. Follow the link [here](https://hacs.xyz/docs/faq/custom_repositories/)
2. Use the custom repo link https://github.com/soloam/ha-fireflyiii-integration
3. Select the category type `integration`
4. Then once it's there (still in HACS) click the INSTALL button
5. Restart Home Assistant
6. Once restarted, in the HA UI go to `Configuration` (the ⚙️ in the lower left) -> `Devices and Services` click `+ Add Integration` and search for `fireflyiii`

## Manual (non-HACS)

<details>
<summary>Instructions</summary>
  
<br>
You probably do not want to do this! Use the HACS method above unless you know what you are doing and have a good reason as to why you are installing manually
<br>
  
1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `fireflyiii_integration`.
4. Download _all_ the files from the `custom_components/fireflyiii_integration/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. Once restarted, in the HA UI go to `Configuration` (the ⚙️ in the lower left) -> `Devices and Services` click `+ Add Integration` and search for `fireflyiii`
</details>

## Configuration is done in the UI
