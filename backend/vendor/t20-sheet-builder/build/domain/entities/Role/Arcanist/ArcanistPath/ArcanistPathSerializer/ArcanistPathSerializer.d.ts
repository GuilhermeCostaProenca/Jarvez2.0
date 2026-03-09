import { type SerializedArcanistPath } from '../../SerializedArcanist';
export declare abstract class ArcanistPathSerializer<S extends SerializedArcanistPath = SerializedArcanistPath> {
    abstract serialize(): S;
}
