"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExoticWeapons = void 0;
const BastardSword_1 = require("./BastardSword");
const ChainofThorns_1 = require("./ChainofThorns");
const DwarfAxe_1 = require("./DwarfAxe");
const Katana_1 = require("./Katana");
const TauricAxe_1 = require("./TauricAxe");
const Whip_1 = require("./Whip");
class ExoticWeapons {
    static getAll() {
        return Object.values(this.map);
    }
    static getByName(name) {
        return this.map[name];
    }
}
exports.ExoticWeapons = ExoticWeapons;
ExoticWeapons.map = {
    whip: Whip_1.Whip,
    bastardSword: BastardSword_1.BastardSword,
    katana: Katana_1.Katana,
    dwarfAxe: DwarfAxe_1.DwarfAxe,
    chainofThorns: ChainofThorns_1.ChainofThorns,
    tauricAxe: TauricAxe_1.TauricAxe,
};
