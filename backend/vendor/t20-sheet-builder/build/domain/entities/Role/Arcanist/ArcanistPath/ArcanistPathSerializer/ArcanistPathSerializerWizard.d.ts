import { type SerializedArcanistWizard } from '../../SerializedArcanist';
import { type ArcanistPathWizard } from '../ArcanisPathWizard';
import { ArcanistPathSerializer } from './ArcanistPathSerializer';
export declare class ArcanistPathSerializerWizard extends ArcanistPathSerializer<SerializedArcanistWizard> {
    private readonly path;
    constructor(path: ArcanistPathWizard);
    serialize(): SerializedArcanistWizard;
}
