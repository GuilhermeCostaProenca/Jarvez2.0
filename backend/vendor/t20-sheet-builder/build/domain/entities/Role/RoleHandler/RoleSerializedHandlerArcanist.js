"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RoleSerializedHandlerArcanist = void 0;
const Arcanist_1 = require("../Arcanist");
const RoleName_1 = require("../RoleName");
const RoleSerializedHandler_1 = require("./RoleSerializedHandler");
class RoleSerializedHandlerArcanist extends RoleSerializedHandler_1.RoleSerializedHandler {
    handle(request) {
        return Arcanist_1.ArcanistFactory.makeFromSerialized(request);
    }
    shouldHandle(request) {
        return request.name === RoleName_1.RoleName.arcanist;
    }
}
exports.RoleSerializedHandlerArcanist = RoleSerializedHandlerArcanist;
