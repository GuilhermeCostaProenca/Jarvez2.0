"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MartialWeapons = void 0;
const BattleAxe_1 = require("./BattleAxe");
const Cutlass_1 = require("./Cutlass");
const Flail_1 = require("./Flail");
const Foil_1 = require("./Foil");
const Halberd_1 = require("./Halberd");
const HandAndAHalfSword_1 = require("./HandAndAHalfSword");
const Hatchet_1 = require("./Hatchet");
const HeavyCrossbow_1 = require("./HeavyCrossbow");
const LongBow_1 = require("./LongBow");
const LongSword_1 = require("./LongSword");
const MountedSpear_1 = require("./MountedSpear");
const Pickaxe_1 = require("./Pickaxe");
const Scimitar_1 = require("./Scimitar");
const Scythe_1 = require("./Scythe");
const Trident_1 = require("./Trident");
const WarAxe_1 = require("./WarAxe");
const WarHammer_1 = require("./WarHammer");
class MartialWeapons {
    static getAll() {
        return Object.values(this.map);
    }
    static getByName(name) {
        return this.map[name];
    }
}
exports.MartialWeapons = MartialWeapons;
MartialWeapons.map = {
    warAxe: WarAxe_1.WarAxe,
    battleAxe: BattleAxe_1.BattleAxe,
    cutlass: Cutlass_1.Cutlass,
    flail: Flail_1.Flail,
    foil: Foil_1.Foil,
    halberd: Halberd_1.Halberd,
    longSword: LongSword_1.LongSword,
    handAndaHalfSword: HandAndAHalfSword_1.HandAndaHalfSword,
    hatchet: Hatchet_1.Hatchet,
    heavyCrossbow: HeavyCrossbow_1.HeavyCrossbow,
    longBow: LongBow_1.LongBow,
    mountedSpear: MountedSpear_1.MountedSpear,
    pickaxe: Pickaxe_1.Pickaxe,
    scimitar: Scimitar_1.Scimitar,
    scythe: Scythe_1.Scythe,
    trident: Trident_1.Trident,
    warHammer: WarHammer_1.WarHammer,
};
