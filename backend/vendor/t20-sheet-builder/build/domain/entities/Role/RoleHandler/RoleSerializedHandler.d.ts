import { type RoleInterface, type SerializedRole } from '../..';
import { Handler } from '../../../../common/handler/Handler';
export declare abstract class RoleSerializedHandler<T extends SerializedRole> extends Handler<SerializedRole, RoleInterface> {
    protected abstract handle(request: T): RoleInterface;
}
