import { type RoleInterface } from './RoleInterface';
import { type SerializedRole, type SerializedRoles } from './SerializedRole';
/**
* @deprecated Use `role.serialize()` instead
*/
export declare abstract class RoleSerializer<S extends SerializedRoles> {
    readonly role: RoleInterface<S>;
    constructor(role: RoleInterface<S>);
    serialize(): SerializedRole<S>;
    protected abstract serializeRole(): S;
}
