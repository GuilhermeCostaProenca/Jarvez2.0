import { type SerializedArcanist } from '../Arcanist';
import { type RoleInterface } from '../RoleInterface';
import { type SerializedRole } from '../SerializedRole';
import { RoleSerializedHandler } from './RoleSerializedHandler';
export declare class RoleSerializedHandlerArcanist extends RoleSerializedHandler<SerializedRole<SerializedArcanist>> {
    protected handle(request: SerializedRole<SerializedArcanist>): RoleInterface;
    protected shouldHandle(request: SerializedRole<SerializedArcanist>): boolean;
}
