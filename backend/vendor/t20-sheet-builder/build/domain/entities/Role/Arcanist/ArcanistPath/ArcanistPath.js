"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPath = exports.ArcanistPathName = void 0;
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
var ArcanistPathName;
(function (ArcanistPathName) {
    ArcanistPathName["wizard"] = "wizard";
    ArcanistPathName["sorcerer"] = "sorcerer";
    ArcanistPathName["mage"] = "mage";
})(ArcanistPathName || (exports.ArcanistPathName = ArcanistPathName = {}));
class ArcanistPath extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.arcanistPath);
    }
}
exports.ArcanistPath = ArcanistPath;
