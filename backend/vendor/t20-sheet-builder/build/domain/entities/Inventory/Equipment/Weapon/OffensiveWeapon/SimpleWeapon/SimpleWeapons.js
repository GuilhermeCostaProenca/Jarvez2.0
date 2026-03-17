"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SimpleWeapons = void 0;
const Sickle_1 = require("./Sickle");
const Assegai_1 = require("./Assegai");
const Baton_1 = require("./Baton");
const Club_1 = require("./Club");
const Dagger_1 = require("./Dagger");
const LightCrossbow_1 = require("./LightCrossbow");
const Mace_1 = require("./Mace");
const Pike_1 = require("./Pike");
const ShortSword_1 = require("./ShortSword");
const Shortbow_1 = require("./Shortbow");
const Sling_1 = require("./Sling");
const Spear_1 = require("./Spear");
const Staff_1 = require("./Staff");
const Horns_1 = require("./Horns");
class SimpleWeapons {
    static getAll() {
        return Object.values(this.map);
    }
    static getByName(name) {
        return this.map[name];
    }
}
exports.SimpleWeapons = SimpleWeapons;
SimpleWeapons.map = {
    assegai: Assegai_1.Assegai,
    baton: Baton_1.Baton,
    club: Club_1.Club,
    dagger: Dagger_1.Dagger,
    horns: Horns_1.Horns,
    lightCrossbow: LightCrossbow_1.LightCrossbow,
    mace: Mace_1.Mace,
    pike: Pike_1.Pike,
    sickle: Sickle_1.Sickle,
    shortbow: Shortbow_1.Shortbow,
    shortSword: ShortSword_1.ShortSword,
    sling: Sling_1.Sling,
    spear: Spear_1.Spear,
    staffStick: Staff_1.StaffStick,
};
