"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Roles = void 0;
const Arcanist_1 = require("./Arcanist");
const Barbarian_1 = require("./Barbarian/Barbarian");
const Bard_1 = require("./Bard");
const Buccaneer_1 = require("./Buccaneer/Buccaneer");
const Cleric_1 = require("./Cleric");
const Druid_1 = require("./Druid");
const Fighter_1 = require("./Fighter");
const Inventor_1 = require("./Inventor");
const Knight_1 = require("./Knight");
const Noble_1 = require("./Noble");
const Paladin_1 = require("./Paladin");
const Ranger_1 = require("./Ranger");
const Rogue_1 = require("./Rogue");
const RoleName_1 = require("./RoleName");
const Warrior_1 = require("./Warrior");
class Roles {
    static getAll() {
        return Object.values(Roles.map);
    }
    static get(roleName) {
        return Roles.map[roleName];
    }
}
exports.Roles = Roles;
Roles.map = {
    [RoleName_1.RoleName.arcanist]: Arcanist_1.Arcanist,
    [RoleName_1.RoleName.warrior]: Warrior_1.Warrior,
    [RoleName_1.RoleName.barbarian]: Barbarian_1.Barbarian,
    [RoleName_1.RoleName.buccaneer]: Buccaneer_1.Buccaneer,
    [RoleName_1.RoleName.bard]: Bard_1.Bard,
    [RoleName_1.RoleName.ranger]: Ranger_1.Ranger,
    [RoleName_1.RoleName.knight]: Knight_1.Knight,
    [RoleName_1.RoleName.cleric]: Cleric_1.Cleric,
    [RoleName_1.RoleName.druid]: Druid_1.Druid,
    [RoleName_1.RoleName.inventor]: Inventor_1.Inventor,
    [RoleName_1.RoleName.rogue]: Rogue_1.Rogue,
    [RoleName_1.RoleName.fighter]: Fighter_1.Fighter,
    [RoleName_1.RoleName.noble]: Noble_1.Noble,
    [RoleName_1.RoleName.paladin]: Paladin_1.Paladin,
};
