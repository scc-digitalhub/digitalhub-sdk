package it.smartcommunitylabdhub.core.components.runnables.events;

import it.smartcommunitylabdhub.core.components.runnables.interfaces.Message;
import it.smartcommunitylabdhub.core.models.dtos.RunDTO;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class RunMessage implements Message {
    private RunDTO runDTO;
}