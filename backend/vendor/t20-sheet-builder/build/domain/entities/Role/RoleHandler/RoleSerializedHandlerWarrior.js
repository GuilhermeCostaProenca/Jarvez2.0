"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RoleSerializedHandlerWarrior = void 0;
const RoleName_1 = require("../RoleName");
const Warrior_1 = require("../Warrior");
const RoleSerializedHandler_1 = require("./RoleSerializedHandler");
class RoleSerializedHandlerWarrior extends RoleSerializedHandler_1.RoleSerializedHandler {
    handle(request) {
        return new Warrior_1.Warrior(request.selectedSkillsByGroup);
    }
    shouldHandle(request) {
        return request.name === RoleName_1.RoleName.warrior;
    }
}
exports.RoleSerializedHandlerWarrior = RoleSerializedHandlerWarrior;
