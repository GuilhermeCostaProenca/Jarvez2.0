import { type RoleInterface } from '../RoleInterface';
import { type SerializedRole, type SerializedWarrior } from '../SerializedRole';
import { RoleSerializedHandler } from './RoleSerializedHandler';
export declare class RoleSerializedHandlerWarrior extends RoleSerializedHandler<SerializedRole<SerializedWarrior>> {
    protected handle(request: SerializedRole<SerializedWarrior>): RoleInterface;
    protected shouldHandle(request: SerializedRole<SerializedWarrior>): boolean;
}
