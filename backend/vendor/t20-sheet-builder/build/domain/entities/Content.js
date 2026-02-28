"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Content = void 0;
/* eslint-disable @typescript-eslint/naming-convention */
const Devotion_1 = require("./Devotion");
const Armors_1 = require("./Inventory/Equipment/Weapon/DefensiveWeapon/Armor/Armors");
const HeavyArmors_1 = require("./Inventory/Equipment/Weapon/DefensiveWeapon/Armor/HeavyArmor/HeavyArmors");
const LightArmors_1 = require("./Inventory/Equipment/Weapon/DefensiveWeapon/Armor/LightArmor/LightArmors");
const ExoticWeapons_1 = require("./Inventory/Equipment/Weapon/OffensiveWeapon/ExoticWeapon/ExoticWeapons");
const FireArmWeapons_1 = require("./Inventory/Equipment/Weapon/OffensiveWeapon/FireArmWeapon/FireArmWeapons");
const MartialWeapons_1 = require("./Inventory/Equipment/Weapon/OffensiveWeapon/MartialWeapon/MartialWeapons");
const SimpleWeapons_1 = require("./Inventory/Equipment/Weapon/OffensiveWeapon/SimpleWeapon/SimpleWeapons");
const Origin_1 = require("./Origin");
const Power_1 = require("./Power");
const Powers_1 = require("./Power/Powers");
const Race_1 = require("./Race");
const ArcanistPathWizardFocuses_1 = require("./Role/Arcanist/ArcanistPath/ArcanisPathWizard/ArcanistPathWizardFocuses");
const Roles_1 = require("./Role/Roles");
const Spell_1 = require("./Spell");
exports.Content = {
    getDeities: () => Devotion_1.Deities,
    getHeavyArmors: () => HeavyArmors_1.HeavyArmors,
    getLightArmors: () => LightArmors_1.LightArmors,
    getExoticWeapons: () => ExoticWeapons_1.ExoticWeapons,
    getFireArmWeapons: () => FireArmWeapons_1.FireArmWeapons,
    getMartialWeapons: () => MartialWeapons_1.MartialWeapons,
    getSimpleWeapons: () => SimpleWeapons_1.SimpleWeapons,
    getOrigins: () => Origin_1.Origins,
    getTormentaPowers: () => Power_1.TormentaPowers,
    getPowers: () => Powers_1.Powers,
    getRaces: () => Race_1.Races,
    getRoles: () => Roles_1.Roles,
    getArcanistPathWizardFocuses: () => ArcanistPathWizardFocuses_1.ArcanistPathWizardFocuses,
    getSpells: () => Spell_1.Spells,
    getArmors: () => Armors_1.Armors,
};
